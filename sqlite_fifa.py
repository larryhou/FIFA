#!/usr/bin/env python3
import sqlite3, enum, os, time, argparse, sys, io, hashlib
import typing

class script_commands(object):
    update_sqlite = 'update-sqlite'
    search_match = 'search-match'

    @classmethod
    def option_choices(cls)->[str]:
        choice_list = []
        for name, value in vars(cls).items():
            if name.replace('_', '-') == value: choice_list.append(value)
        return choice_list

class MatchStage(enum.Enum):
    group, knock, quarter, semi, third, final = range(6)

def fetch_sqlite(data_filepath:str = None)->sqlite3.Connection:
    database_name = 'fifa.sqlite'
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()
    result = cursor.execute('SELECT name FROM sqlite_master WHERE type=\'table\' AND name=?', ('matches',))
    if not result.fetchall():
        cursor.execute('''
            CREATE TABLE matches
            (uuid text NOT NULL UNIQUE ON CONFLICT IGNORE, 
             date INTEGER NOT NULL, year INTEGER NOT NULL, time text NOT NULL,
             team text NOT NULL, 
             opponent text NOT NULL, 
             score INTEGER NOT NULL, 
             opponent_score INTEGER NOT NULL, 
             stage INTEGER NOT NULL, group_name text, stadium text, venue text)
        ''')
        connection.commit()
    if not (data_filepath and os.path.exists(data_filepath)): return connection
    stage_map = vars(MatchStage)
    record_list = []
    with open(data_filepath, 'r+') as fp:
        for line in fp.readlines():
            data = [x.strip() for x in line.split(',')]
            match_time = time.strptime(data[0], '%Y-%m-%d %H:%M')
            date = time.mktime(match_time)
            team = data[1]
            md5 = hashlib.md5()
            md5.update((data[0] + team).encode('utf-8'))
            uuid = md5.hexdigest()
            opponent = data[2]
            score = int(data[3])
            opponent_score = int(data[4])
            match_type = data[5]
            group_name = match_type if len(match_type) == 1 else None
            if group_name:
                stage = MatchStage.group
            else:
                stage = stage_map.get(match_type.lower())
            stadium = data[6]
            venue = data[7]
            item = [uuid, date, match_time.tm_year, time.strftime('%Y-%m-%dT%H:%M:%S', match_time), team, opponent, score,
                    opponent_score, stage.value, group_name, stadium, venue]
            param_count = len(item)
            record_list.append(tuple(item))
            item[4:4+4] = [opponent, team, opponent_score, score]
            md5 = hashlib.md5()
            md5.update((data[0] + opponent).encode('utf-8'))
            item[0] = md5.hexdigest()
            assert len(item) == param_count, item
            record_list.append(tuple(item))
    command = 'INSERT INTO matches VALUES ({})'.format(','.join(['?'] * len(item)))
    cursor = connection.cursor()
    cursor.executemany(command, record_list)
    connection.commit()
    return connection

class ArgumentOptions(object):
    def __init__(self, data):
        self.command = data.command # type: str
        self.file_path = data.file_path # type: str
        self.team = data.team # type: str

def table_print(data_list:typing.List[typing.Tuple]):
    width_list = [0] * len(data_list[0])
    for r in range(len(data_list)):
        record = data_list[r]
        alias_record = []
        for n in range(len(record)):
            item = str(record[n])
            width_list[n] = max(width_list[n], len(item))
            alias_record.append(item)
        data_list[r] = alias_record
    buffer = io.StringIO()
    for n in range(len(width_list)):
        buffer.write('{{:{}s}} | '.format(width_list[n]))
    buffer.seek(0)
    record_format = buffer.read() # type: str
    for record in  data_list:
        print(record_format.format(*record))

def search_match(options:ArgumentOptions, connection:sqlite3.Connection):
    cursor = connection.cursor()
    result = cursor.execute('''SELECT date,team,opponent,score,opponent_score,stage,group_name 
        FROM matches WHERE team=? ORDER BY date DESC''', (options.team,))
    match_list = result.fetchall()
    if len(match_list) > 0:
        result = []
        for item in match_list:
            date, team, opponent, score, opponent_score, stage, group_name = item
            date = time.strftime('%Y-%m-%d', time.localtime(date))
            stage = ':{}:'.format(group_name) if group_name else MatchStage(stage).name
            result.append((date, team, opponent, score, opponent_score, stage))
        table_print(data_list=result)
        return
    buffer = io.StringIO()
    buffer.write('%')
    for char in options.team:
        buffer.write(char)
        buffer.write('%')
    buffer.seek(0)
    result = cursor.execute('SELECT DISTINCT team FROM matches WHERE team LIKE ?', (buffer.read(),))
    team_list = [x[0] for x in result.fetchall()]
    if len(team_list) > 0:
        print('MAYBE < {} >'.format(' | '.join(team_list)))

def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--command', '-c', default=script_commands.search_match, choices=script_commands.option_choices())
    arguments.add_argument('--team', '-t', help='team name for search')
    arguments.add_argument('--file-path', '-f', help='history data file with csv format')
    options = ArgumentOptions(data=arguments.parse_args(sys.argv[1:]))

    command = options.command
    if command == script_commands.update_sqlite:
        assert os.path.exists(options.file_path)
        fetch_sqlite(data_filepath=options.file_path).close()
    elif command == script_commands.search_match:
        assert options.team
        connection = fetch_sqlite(data_filepath=options.file_path)
        search_match(options, connection)
        connection.close()

if __name__ == '__main__':
    main()
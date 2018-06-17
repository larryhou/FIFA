#!/usr/bin/env python3

import time, argparse, sys, os
from typing import List, Dict

class script_commands(object):
    dump  = ('d', 'dump')
    find  = ('f', 'find')
    stat  = ('s', 'stat')

    @classmethod
    def get_option_choices(cls)->List[str]:
        choice_list = []
        for name, value in vars(cls).items():
            if name.startswith('__') or name.endswith('__') or not isinstance(value, tuple): continue
            choice_list.extend(list(value))
        return choice_list

class MatchSummary(object):
    def __init__(self, data):
        if not data: return
        data = data[1:]
        self.date = time.strptime(data[0], '%Y-%m-%d %H:%M')
        self.team = data[1]
        self.opponent = data[2]
        self.score = int(data[3])
        self.opponent_score = int(data[4])
        self.group = data[5]
        self.stadium = data[6]
        self.venue = data[7]

    def reverse(self):
        item = MatchSummary(data=None)
        item.date = self.date
        item.team, item.opponent, item.group = self.opponent, self.team, self.group
        item.score, item.opponent_score = self.opponent_score, self.score
        item.stadium, item.venue = self.stadium, self.venue
        return item

    def __repr__(self):
        return '%s|%s|%s|%d|%d|%s|%s|%s'%(time.strftime('%Y-%m-%d', self.date),
                                                self.team, self.opponent, self.score, self.opponent_score,
                                                self.group, self.stadium, self.venue)

def load(file_path:str)->List[MatchSummary]:
    assert os.path.exists(file_path)
    dup_map, match_list = {}, []
    with open(file_path, 'r+') as fp:
        for line in fp.readlines():
            if not line: continue
            uuid = line[:7]
            if uuid in dup_map: continue
            dup_map[uuid] = True
            item = MatchSummary(data=line[:-1].split('|'))
            match_list.append(item)
    def cmp(a:MatchSummary, b:MatchSummary):
        if a.date.tm_year != b.date.tm_year:
            return -1 if a.date.tm_year > b.date.tm_year else 1
        return 1 if a.date > b.date else -1
    from functools import cmp_to_key
    match_list.sort(key=cmp_to_key(cmp))
    return match_list

def filter_year_list(stat_map:[int, List], year:int, span:int):
    year_list = list(stat_map.keys())
    temp_list = []
    for n in range(len(year_list)):
        y = year_list[n]
        if span == 0:
            if y < year: continue
        elif span > 0:
            if y > year + span: continue
        elif span < 0:
            if y < year + span: continue
        temp_list.append(y)
    temp_list.sort(reverse=True)
    return temp_list

def dump_stat_map(stat_map:Dict[int, List], year_list:List[int]):
    csv_sheet = []
    matY, matX, offset = 0, 0, 0
    num_of_horizon = 3
    max_stat_count = 0
    header = ['', '进', '丢', '场', '胜', '平', '负']
    for year in year_list:
        year_stat_list = stat_map.get(year)
        stat_count = len(year_stat_list)
        max_stat_count = max(stat_count, max_stat_count)
        for n in range(stat_count + 1):
            row = n + offset
            while row >= len(csv_sheet): csv_sheet.append([])
            cell_list = csv_sheet[row]
            if n == 0:
                header[0] = '%d'%year
                cell_list.extend(header)
                continue
            if matX * 7 > len(cell_list):
                cell_list.extend(['']*(matX-1)*7)
            stat = year_stat_list[n - 1]
            cell_list.extend(stat)
        matX += 1
        if matX == num_of_horizon:
            matX %= num_of_horizon
            matY += 1
            offset += max_stat_count + 1
            max_stat_count = 0
    for row in csv_sheet:
        print(','.join([str(x) for x in row]))

def generate_stat_map(match_list:List[MatchSummary]):
    season_map, stat_map = {}, {}
    for item in match_list:
        year = item.date.tm_year
        if year not in season_map: season_map[year] = []
        season_map[year].extend([item, item.reverse()])
    for year, season_match_list in season_map.items():
        year_stat_map = anlaysis_team_stat(season_match_list)
        stat_map[year] = year_stat_map
    return stat_map

def anlaysis_team_stat(match_list:List[MatchSummary]):
    stat_map = {}
    for item in match_list:
        if item.team not in stat_map:
            stat_map[item.team] = [0]*6
        stat = stat_map[item.team]
        stat[0] += item.score
        stat[1] += item.opponent_score
        stat[2] += 1
        diff = item.score - item.opponent_score
        if diff > 0: stat[3] += 1
        if not diff: stat[4] += 1
        if diff < 0: stat[5] += 1
    result_list = []
    for name, stat in stat_map.items():
        stat.insert(0, name)
        result_list.append(stat)
    from operator import itemgetter
    result_list.sort(key=itemgetter(3, 4, 5), reverse=True)
    return result_list

def find_team_stat(match_list:List[MatchSummary], team, year_list:List[int]):
    for n in range(len(match_list)):
        item = match_list[n]
        if item.date.tm_year in year_list:
            if item.team.find(team) >= 0:
                print(item)
            elif item.opponent.find(team) >=0:
                print(item.reverse())

def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--file-path', '-f', required=True)
    arguments.add_argument('--team', '-t')
    arguments.add_argument('--year', '-y', type=int, default=0)
    arguments.add_argument('--span', '-s', type=int, default=0)
    arguments.add_argument('--command', '-c',
                           choices=script_commands.get_option_choices(),
                           default=script_commands.stat[0])

    options = arguments.parse_args(sys.argv[1:])
    match_list = load(options.file_path)
    command = options.command
    stat_map = generate_stat_map(match_list)
    year_list = filter_year_list(stat_map, options.year, options.span)
    if command in script_commands.dump:
        for item in match_list:
            if item.date.tm_year in year_list: print(item)
    elif command in script_commands.stat:
        dump_stat_map(stat_map, year_list)
    elif command in script_commands.find:
        find_team_stat(match_list, options.team, year_list)
    else:
        raise NotImplementedError()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
from sqlite_fifa import MatchStage, table_print

PROMOTED_TEAMS = [
    'France',
    'Argentina',
    'Uruguay',
    'Portugal',
    'Spain',
    'Russia',
    'Croatia',
    'Denmark',
    'Brazil',
    'Mexico',
    'Belgium',
    'Japan',
    'Sweden',
    'Switzerland',
    'Colombia',
    'England'
]

def main():
    import sqlite3
    connection = sqlite3.connect('fifa.sqlite')
    cursor = connection.cursor()
    result = cursor.execute('SELECT team,score,opponent_score,stage,group_name FROM matches WHERE year=2018')
    column_header = ['', 'MP', 'W', 'D', 'L', 'GF', 'GA', '+/-', 'PTS', '', '']
    match_map = {} # type: dict[str, list]
    for item in result.fetchall():
        team, score, opponent_score, stage, group_name = item
        stage = MatchStage(stage)
        if team not in match_map: match_map[team] = [team] + [0] * 8 + [group_name, '★' if team in PROMOTED_TEAMS else ' ']
        stat = match_map[team]
        stat[1] += 1
        netscore = score - opponent_score
        stat[2] += 1 if netscore  > 0 else 0
        stat[3] += 1 if netscore == 0 else 0
        stat[4] += 1 if netscore  < 0 else 0
        stat[5] += score
        stat[6] += opponent_score
        stat[7] += netscore
        if stage == MatchStage.group:
            stat[8] += 3 if netscore > 0 else (1 if netscore == 0 else 0)
    stat_list = []
    for _, stat in match_map.items():
        stat_list.append(stat)
    from operator import itemgetter
    stat_list.sort(key=itemgetter(1, 2, 3, 5), reverse=True)
    stat_list.insert(0, column_header)
    table_print(stat_list, print_header=True)

if __name__ == '__main__':
    main()
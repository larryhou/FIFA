#!/usr/bin/env python3
#encoding:utf-8

import argparse, sys, os, re, time, enum
from typing import List

class FieldType(enum.Enum):
    home, away, neutral = range(3)
class WinType(enum.Enum):
    win, lose, draw = range(3)

class MatchRecordItem(object):
    def __init__(self, data):
        if not data: return
        self.date = time.strptime(data[0], '%Y-%m-%d')
        self.team = data[1]
        self.oponent = data[2]
        self.score = int(data[3])
        self.opponent_score = int(data[4])
        self.match = data[5]
        self.city = data[6]
        self.country = data[7]
        self.field = FieldType.neutral if data[8] == 'TRUE' else FieldType.home
        diff = self.score - self.opponent_score
        self.type = WinType.win if diff > 0 else (WinType.draw if diff == 0 else WinType.lose)

    def reverse(self):
        item = MatchRecordItem(None)
        item.date = self.date
        item.team, item.oponent = self.oponent, self.team
        item.score, item.opponent_score = self.opponent_score, self.score
        item.match = self.match
        item.city, item.country = self.city, self.country
        item.field = FieldType.away
        item.type = WinType(1 - self.type.value) if self.score != self.opponent_score else WinType.draw
        return item

    def __repr__(self):
        return '%s|%s|%s|%d|%d|%s|%s|%s|%s|%s'%(time.strftime('%Y-%m-%d', self.date),
                                             self.team, self.oponent, self.score, self.opponent_score,
                                             self.match, self.city, self.country, self.field.name, self.type.name)

def load_data(file_path: str)->List[MatchRecordItem]:
    assert os.path.exists(file_path)
    record_list, record_map = [], {}
    group_name_list = ('team', 'city', 'country', 'match')
    for name in group_name_list:
        record_map[name] = {}
    with open(file_path, 'r+') as fp:
        fp.readline() # skip column field names
        for line in fp.readlines():
            if not line: continue
            item = MatchRecordItem(re.split(r'\s*,\s*', line[:-1]))
            for it in [item, item.reverse()]:
                for name in group_name_list:
                    data_map = record_map.get(name)
                    field_value = it.__getattribute__(name)
                    if field_value not in data_map: data_map[field_value] = []
                    data_map[field_value].append(it)
                record_list.append(it)
    return record_list, record_map

def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--file-path', '-f', required=True, help='match history score data file')
    arguments.add_argument('--team', '-t', help='football team')
    arguments.add_argument('--year', '-y', type=int, help='match year number')
    arguments.add_argument('--match', '-m', help='match name (FIFA etc.)')
    arguments.add_argument('--country', '-c', help='country where match took place')
    arguments.add_argument('--city', '-i', help='city where match took place')
    options = arguments.parse_args(sys.argv[1:])
    record_list, record_map = load_data(options.file_path)
    filter_name_list = []
    if options.team:
        filter_name_list.append('team')
    if options.match:
        filter_name_list.append('match')
    if options.city:
        filter_name_list.append('city')
    if options.country:
        filter_name_list.append('country')
    if not filter_name_list:
        result_list = record_list
    else:
        filter_name = filter_name_list[0]
        result_list = record_map.get(filter_name).get(options.__getattribute__(filter_name))
        del filter_name_list[0]
        if filter_name_list:
            for filter_name in filter_name_list:
                temp_list = []
                for n in range(len(result_list)):
                    item = result_list[n]
                    if item.__getattribute__(filter_name) == options.__getattribute__(filter_name):
                        temp_list.append(item)
                result_list = temp_list
    temp_list = []
    if options.year:
        for n in range(len(result_list)):
            item = result_list[n]
            if item.date.tm_year == options.year: temp_list.append(item)
        result_list = temp_list
    for n in range(len(result_list)):
        print(result_list[n])

if __name__ == '__main__':
    main()
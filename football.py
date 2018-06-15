#!/usr/bin/env python3
#encoding:utf-8

import argparse, sys, os, re, time, enum
from typing import List,Dict
from operator import attrgetter, itemgetter

storage = {}

EURO_CUP = 'UEFA Euro'
FIFA_CUP = 'FIFA World Cup'
FIFA_CUP_QUALIFICATION = 'FIFA World Cup qualification'

class FieldType(enum.Enum):
    home, away, neutral = range(3)
class WinType(enum.Enum):
    win, lose, draw = range(3)

class field_names(object):
    team = 'team'
    city = 'city'
    country = 'country'
    match = 'match'

def get_field_value(field_name:str, index:int)->str:
    index_map = storage.get(field_name)
    return index_map.get(index)

def get_field_index(field_name:str, value:str)->int:
    counter_name = '__index__'
    if field_name not in storage: storage[field_name] = {}
    index_map = storage.get(field_name)
    if counter_name not in index_map: index_map[counter_name] = 1
    if value not in index_map:
        index = index_map[counter_name]
        index_map[counter_name] = index + 1
        index_map[value] = index
        index_map[index] = value
        return index
    else:
        return index_map.get(value)

class MatchRecordItem(object):
    def __init__(self, data):
        if not data: return
        self.date = time.strptime(data[0], '%Y-%m-%d')
        self.team = data[1]
        self.opponent = data[2]
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
        item.team, item.opponent = self.opponent, self.team
        item.score, item.opponent_score = self.opponent_score, self.score
        item.match = self.match
        item.city, item.country = self.city, self.country
        item.field = FieldType.neutral if self.field == FieldType.neutral else FieldType.away
        item.type = WinType(1 - self.type.value) if self.score != self.opponent_score else WinType.draw
        return item

    def __repr__(self):
        return '%s|%s|%s|%d|%d|%s|%s|%s|%s'%(time.strftime('%Y-%m-%d', self.date),
                                                self.team, self.opponent, self.score, self.opponent_score,
                                                self.match, self.country, self.field.name, self.type.name)

def load_data(file_path: str)->List[MatchRecordItem]:
    assert os.path.exists(file_path)
    record_list, record_map = [], {}
    group_name_list = (field_names.team, field_names.match, field_names.country, field_names.city)
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


def assert_field_name(data_map:Dict[str, List[MatchRecordItem]], field_name:str, value:str):
    group_map = data_map.get(field_name)
    if value not in group_map:
        recommend_list = []
        for name in group_map.keys():
            if str(name).find(value) >= 0: recommend_list.append(name)
        print('[NOT_FOUND] --%s=%r,'%(field_name, value),', '.join(recommend_list))
        sys.exit()

def analysis_euro(data_map:Dict[str,List[MatchRecordItem]]):
    item_list = data_map[field_names.match].get(EURO_CUP)
    temp_list = []
    for n in range(len(item_list)):
        item = item_list[n]
        if item.date.tm_year == 2016: temp_list.append(item)
    print('[%s]' % EURO_CUP)
    analysis_data(temp_list)

def analysis_fifa(data_map:Dict[str,List[MatchRecordItem]]):
    item_list = data_map[field_names.match].get(FIFA_CUP)
    temp_list = []
    for n in range(len(item_list)):
        item = item_list[n]
        if item.date.tm_year == 2014: temp_list.append(item)
    print('[%s]' % FIFA_CUP)
    analysis_data(temp_list)

def analysis_fifa_qualification(data_map:Dict[str,List[MatchRecordItem]]):
    item_list = data_map[field_names.match].get(FIFA_CUP_QUALIFICATION)
    temp_list = []
    for n in range(len(item_list)):
        item = item_list[n]
        if item.date.tm_year >= 2014: temp_list.append(item)
    print('[%s]'%FIFA_CUP_QUALIFICATION)
    analysis_data(temp_list)

def analysis_data(data_list:List[MatchRecordItem]):
    stat_map = {}
    for n in range(len(data_list)):
        item = data_list[n]
        if item.team not in stat_map: stat_map[item.team] = [0]*5
        stat = stat_map[item.team]
        stat[0] += item.score
        if item.score > item.opponent_score:
            stat[1] += item.score - item.opponent_score
            stat[2] += 1
        elif item.score < item.opponent_score:
            stat[4] += 1
        else:
            stat[3] += 1
    result = []
    for name, stat in stat_map.items():
        stat.insert(0, name)
        result.append(stat)
    result.sort(key=itemgetter(3,2,1), reverse=True)
    for n in range(len(result)):
        item = result[n]
        print(','.join([str(x) for x in item]))

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
        filter_name_list.append(field_names.team)
        assert_field_name(record_map, field_names.team, options.team)
    if options.match:
        filter_name_list.append(field_names.match)
        assert_field_name(record_map, field_names.match, options.match)
    if options.city:
        filter_name_list.append(field_names.city)
    if options.country:
        filter_name_list.append(field_names.country)
        assert_field_name(record_map, field_names.country, options.country)
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
            if item.date.tm_year >= options.year: temp_list.append(item)
        result_list = temp_list
    for n in range(len(result_list)):
        print(result_list[n])
    sys.exit()
    analysis_fifa(data_map=record_map)
    analysis_euro(data_map=record_map)
    analysis_fifa_qualification(data_map=record_map)

if __name__ == '__main__':
    main()
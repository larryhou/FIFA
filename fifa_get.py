#!/usr/bin/env python3

import requests, pyquery, enum, re, json, time

team_abbrs = {}

class MatchGroup(enum.Enum):
    A,B,C,D,E,F,G,H,Knock,Quarter,Semi,Third,Final = range(1,14)

def decode_match_time(value:str, timeshift:float)->str:
    datetime = time.strptime(value.strip(), '%d %b %Y - %H:%M Local time')
    if timeshift > 0:
        datetime = time.localtime(time.mktime(datetime) - (time.timezone + timeshift))
    return time.strftime('%Y-%m-%d %H:%M', datetime)

def decode_match_group(value:str)->MatchGroup:
    value = value.strip()
    if re.match(r'^Group \w$', value):
        name = value.split(' ')[-1]
        if re.match(r'^\d+$', name): return MatchGroup(int(name))
        return vars(MatchGroup).get(name)
    if value == 'Round of 16': return MatchGroup.Knock
    if value.startswith('Quarter'): return MatchGroup.Quarter
    if value.startswith('Semi'): return MatchGroup.Semi
    if re.search(r'Third', value, re.IGNORECASE): return MatchGroup.Third
    return MatchGroup.Final

def dump_worldcup(url:str):
    response = requests.get(url)
    content = response.text.encode(response.apparent_encoding).decode('utf-8')
    jq = pyquery.PyQuery(content)
    for result in jq.find('div .mu.result'):
        item = pyquery.PyQuery(result)
        datetime = decode_match_time(item.find('.mu-i-datetime').text(), timeshift=0)
        group = decode_match_group(item.find('.mu-i-group').text())
        stadium = re.sub(r',\s*', r'/', item.find('.mu-i-stadium').text())
        venue = re.sub(r',\s*', r'/', item.find('.mu-i-venue').text())
        team_home = item.find('.t.home .t-nText').text()
        team_home_code = item.find('.t.home .t-nTri').text()
        if team_home_code not in team_abbrs:
            team_abbrs[team_home_code] = team_home
        team_away = item.find('.t.away .t-nText').text()
        team_away_code = item.find('.t.away .t-nTri').text()
        if team_away_code not in team_abbrs:
            team_abbrs[team_away_code] = team_away
        score = [x for x in item.find('.s-scoreText').text().split('-')]
        record = []
        record.extend([datetime, team_home, team_away])
        record.extend(score)
        record.append(group.name)
        record.extend([stadium, venue])
        print(','.join(record))

def dump_worldcup_score(url:str):
    response = requests.get(url)
    content = response.text.encode(response.apparent_encoding).decode('utf-8')
    jq = pyquery.PyQuery(content)
    for result in jq.find('div .fi-mu.result'):
        item = pyquery.PyQuery(result)
        timeshift = float(item.find('.fi-s__score').attr('data-timeshiftutc')) * 60
        datetime = decode_match_time(item.find('.fi-mu__info__datetime').text(), timeshift)
        group_data = item.find('.fi__info__group').text()
        if not group_data:
            group_data = item.parent().parent().find('span.fi-mu-list__head__date').text()
        group = decode_match_group(group_data)
        stadium = re.sub(r',\s*', r'/', item.find('.fi__info__stadium').text())
        venue = re.sub(r',\s*', r'/', item.find('.fi__info__venue').text())
        team_home = item.find('.home .fi-t__nText').text()
        team_home_code = item.find('.home .fi-t__nTri').text()
        if team_home_code not in team_abbrs:
            team_abbrs[team_home_code] = team_home
        team_away = item.find('.away .fi-t__nText').text()
        team_away_code = item.find('.away .fi-t__nTri').text()
        if team_away_code not in team_abbrs:
            team_abbrs[team_away_code] = team_away
        score = [x for x in item.find('.fi-s__scoreText').text().split('-')]
        record = []
        record.extend([datetime, team_home, team_away])
        record.extend(score)
        record.append(group.name)
        record.extend([stadium, venue])
        print(','.join(record))

def dump_worldcup_match(url:str):
    response = requests.get(url)
    content = response.text.encode(response.apparent_encoding).decode('utf-8')
    jq = pyquery.PyQuery(content)
    for result in jq.find('div .fi-mu.fixture'):
        item = pyquery.PyQuery(result)
        timeshift = float(item.find('.fi-s__score').attr('data-timeshiftutc')) * 60
        datetime = decode_match_time(item.find('.fi-mu__info__datetime').text(), timeshift)
        group_data = item.find('.fi__info__group').text()
        if not group_data:
            parent = item.parent()
            if not parent.attr('class') == 'fi-mu-list':
                parent = parent.parent()
            group_data = parent.find('span.fi-mu-list__head__date').text()
        group = decode_match_group(group_data)
        stadium = re.sub(r',\s*', r'/', item.find('.fi__info__stadium').text())
        venue = re.sub(r',\s*', r'/', item.find('.fi__info__venue').text())
        team_home = item.find('.home .fi-t__nText').text()
        team_home_code = item.find('.home .fi-t__nTri').text()
        if team_home_code not in team_abbrs:
            team_abbrs[team_home_code] = team_home
        team_away = item.find('.away .fi-t__nText').text()
        team_away_code = item.find('.away .fi-t__nTri').text()
        if team_away_code not in team_abbrs:
            team_abbrs[team_away_code] = team_away
        record = []
        record.extend([datetime, team_home, team_away])
        record.append(group.name)
        record.extend([stadium, venue])
        print(','.join(record))

class script_commands(object):
    fetch_history = 'fetch-history'
    dump_score = 'dump-score'
    dump_match = 'dump-match'

    @classmethod
    def option_choices(cls):
        choice_list = []
        for name, value in vars(cls).items():
            if name.replace('_','-') == value: choice_list.append(value)
        return choice_list

def main():
    import argparse, sys
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--command', '-c', default=script_commands.fetch_history, choices=script_commands.option_choices())
    arguments.add_argument('--page-url', '-u', default='https://www.fifa.com/worldcup/matches/')
    options = arguments.parse_args(sys.argv[1:])
    command = options.command
    if command == script_commands.fetch_history:
        jq = pyquery.PyQuery(url='https://www.fifa.com/fifa-tournaments/statistics-and-records/worldcup/index.html')
        for season in jq.find('.tbl-seasonname a'):
            name = season.get('href').split('/')[-2]
            dump_worldcup(url='https://www.fifa.com/worldcup/archive/%s/matches/index.html'%name)
        print(json.dumps(team_abbrs,ensure_ascii=False, sort_keys=True))
    elif command == script_commands.dump_score:
        assert options.page_url
        dump_worldcup_score(url=options.page_url)
    elif command == script_commands.dump_match:
        assert options.page_url
        dump_worldcup_match(url=options.page_url)

if __name__ == '__main__':
    main()
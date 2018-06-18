#!/usr/bin/env python3

import requests, pyquery, enum, re, json

month_abbrs = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6, Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)
team_abbrs = {}

class MatchGroup(enum.Enum):
    A,B,C,D,E,F,G,H,Knock,Quarter,Semi,Third,Final = range(1,14)

def decode_match_time(value:str)->str:
    items = value.split(' ')
    date, month, year, time = items[0], month_abbrs.get(items[1].title()[:3]), items[2], items[4]
    return '%s-%02d-%s %s'%(year, month, date, time)

def decode_match_group(value:str)->MatchGroup:
    if re.match(r'^Group \w$', value):
        name = value.split(' ')[-1]
        if re.match(r'^\d+$', name): return MatchGroup(int(name))
        return vars(MatchGroup).get(name)
    if value == 'Round of 16': return MatchGroup.Knock
    if value.startswith('Quarter'): return MatchGroup.Quarter
    if value.startswith('Semi'): return MatchGroup.Semi
    if re.search(r'Third', value, re.IGNORECASE): return MatchGroup.Third
    return MatchGroup.Final

def decode_string(value:str)->str:
    return value.encode('ISO-8859-1').decode('utf-8')

def dump_worldcup(url:str):
    content = decode_string(requests.get(url).text)
    jq = pyquery.PyQuery(content)
    for result in jq.find('div .mu.result'):
        item = pyquery.PyQuery(result)
        datetime = decode_match_time(item.find('.mu-i-datetime').text())
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

def main():
    jq = pyquery.PyQuery(url='https://www.fifa.com/fifa-tournaments/statistics-and-records/worldcup/index.html')
    for season in jq.find('.tbl-seasonname a'):
        name = season.get('href').split('/')[-2]
        dump_worldcup(url='https://www.fifa.com/worldcup/archive/%s/matches/index.html'%name)
    print(json.dumps(team_abbrs,ensure_ascii=False, sort_keys=True))

if __name__ == '__main__':
    main()
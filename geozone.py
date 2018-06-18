#!/usr/bin/env python3
import requests, argparse, sys, time

GOOGLE_API_KEY = 'AIzaSyBQ6vtDD_qkk8eQ9BwTt-OTJ9-_RrsNz0w'

def google_geocode_api(address:str):
    params = {'address':address, 'key':GOOGLE_API_KEY}
    response = requests.get(url='https://maps.googleapis.com/maps/api/geocode/json', params=params)
    return response.json()

def google_timezone_api(latitude:float, longitude:float):
    params = {
        'location': '%f,%f'%(latitude, longitude),
        'timestamp': int(time.mktime(time.localtime())),
        'key': GOOGLE_API_KEY
    }
    response = requests.get(url='https://maps.googleapis.com/maps/api/timezone/json', params=params)
    return response.json()

def geo_timezone(address:str):
    location = google_geocode_api(address=address)
    if not location.get('results'): return {}
    gps = location['results'][0]['geometry']['location']
    return google_timezone_api(latitude=gps['lat'], longitude=gps['lng'])

def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--address', '-a', required=True)
    options = arguments.parse_args(sys.argv[1:])
    result = geo_timezone(address=options.address)
    print(result)

if __name__ == '__main__':
    main()
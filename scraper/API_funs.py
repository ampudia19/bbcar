import requests
import time
from datetime import date, datetime
import random
import json
from tqdm import tqdm
import os

from constants import API_KEY, API_KEY2, API_KEY3, API_KEY4, API_KEY5, API_KEY6
from constants import API_KEY7, API_KEY8, API_KEY9, API_KEY10, API_KEY11, API_KEY12
from constants import API_KEY13, API_KEY14, API_KEY15, API_KEY16

API_DICT = {
    'main': API_KEY,
    'aux1': API_KEY2,
    'aux2': API_KEY3,
    'aux3': API_KEY4,
    'aux4': API_KEY5,
    'aux6': API_KEY6,
    'aux7': API_KEY7,
    'aux8': API_KEY8,
    'aux9': API_KEY9,
    'aux10': API_KEY10,
    'aux11': API_KEY11,
    'aux12': API_KEY12,
    'aux13': API_KEY13,
    'aux14': API_KEY14,
    'aux15': API_KEY15,
    'aux16': API_KEY16,
}

#%%
def getRow(trip):
    '''
    Flattens a BlaBlaCar trip object into a plain list.
    '''
    return {
        'url': trip['links']['_front'],
        'from_lat': trip['departure_place']['latitude'],
        'from_lon': trip['departure_place']['longitude'],
        'to_lat': trip['arrival_place']['latitude'],
        'to_lon': trip['arrival_place']['longitude'],
        'car_comfort': trip['car']['comfort_nb_star'] if 'car' in trip else '',
        'car_maker': trip['car']['make'] if 'car' in trip else '',
        'dep_date': trip['departure_date'],
        'distance': trip['distance']['value'],
        'duration': trip['duration']['value'],
        'price': trip['price_with_commission']['value'],
        'seats': trip['seats']
    }


def rotate(d):
    '''
    Function to rotate dictionary values. Takes a dictionary, returns
    another with values displaced one key to the right.
    '''
    keys = d.keys()
    values = list(d.values())
    values = values[1:] + values[:1]
    d = dict(zip(keys, values))
    return d


def getTrips(origin, startdate, dataset, log_dest):
    '''
    Iterates over the BlaBlaCar trip endpoints.
    Checks for multiple page results, rotates keys and returns
    indexed results by department.

    - origin: takes city row
    - startdate: takes a datetime
    - dataset: Frame containing all possible destinations
    - log_dest: Takes a path to dump json results
    
    Returns
    -------
    :trips:

    '''
    trips = []

    # local_dict = API_DICT
    
    iterator = tqdm(dataset[~(dataset.index == origin.index[0])].iterrows())
    
    for i, row in iterator:
        iterator.set_description(f'{origin.Commune}')
        
        # local_dict = rotate(local_dict)
        KEY = random.choice(list(API_DICT.values()))
        page = None
        iterr_list = []

        URL = "https://public-api.blablacar.com/api/v3/trips"
        CUR = "EUR"

        HEADERS = {
            'Content-Type': "application/json",
            'Cache-Control': "no-cache"
        }
        QS_BASE = {
            "key": KEY,
            "currency": CUR,
            "from_coordinate": origin['coord'],
            "to_coordinate": row['coord'],
            "start_local_date": startdate
        }

        querystring = dict(
            **QS_BASE
        )

        url = "https://wtfismyip.com"
        proxy_host = "gate.smartproxy.com"
        proxy_port = "7000"
        proxy_user = "blablacar"
        proxy_password = "blablacar_pass"

        # proxies = {
        #     "https": f"http://user-{proxy_user}:{proxy_password}@{proxy_host}:{proxy_port}/",
        #     "http": f"http://user-{proxy_user}:{proxy_password}@{proxy_host}:{proxy_port}/",
        # }

        rj = None
        
        while rj is None:
            try:
                response = requests.request(
                    "GET",
                    URL,
                    headers=HEADERS,
                    params=querystring,
                    # proxies=proxies
                )
    
                rj = response.json()
    
                iterr_list.extend(rj['trips'])

                time.sleep(random.uniform(0.5,1))
    
                with open(log_dest, 'a') as f:
                    f.write(json.dumps(rj))
    
                while 'next_cursor' in rj:
    
                    time.sleep(random.uniform(0.5,1))
    
                    page = rj['next_cursor']
    
                    querystring = dict(
                        {'from_cursor': page},
                        **QS_BASE
                    )
    
                    response = requests.request(
                        "GET",
                        URL,
                        headers=HEADERS,
                        params=querystring, 
                        timeout=30,
                        # proxies=proxies
                    )
    
                    rj = response.json()
    
                    iterr_list.extend(rj['trips'])
    
                    with open(log_dest, 'a') as f:
                        f.write(json.dumps(rj))
    
                trips.append(
                    tuple([i, datetime.fromtimestamp(time.time()), iterr_list])
                )

                time.sleep(
                    random.uniform(1, 2)
                )
    
            except ValueError:  # includes simplejson.decoder.JSONDecodeError
                print(f'Decoding JSON has failed for trips from {row.Commune}')
                with open(log_dest, 'a') as f:
                    f.write('ValueError')
                    
                trips.append(tuple([i, datetime.fromtimestamp(time.time()), None]))
    
            except KeyError as e:
                remaining_calls = response.headers['x-ratelimit-remaining-day']
                print(e, f'with KEY {KEY}. Remaining calls: {remaining_calls}')
                if remaining_calls != 0:  
                    time.sleep(15)
                if remaining_calls == 0:
                    time.sleep(15)
                    KEY = local_dict['aux1']
                    QS_BASE['key'] = KEY
                continue
                
            except ConnectionError as e:
                print(e)
                pass

    return trips

def uniquifier(path):
    filename, extension = os.path.splitext(path)
    counter = 0
    path = filename + "_" + str(counter) + extension

    while os.path.exists(path):
        counter += 1
        path = filename + "_" + str(counter) + extension

    return path, counter

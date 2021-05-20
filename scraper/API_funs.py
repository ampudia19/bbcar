import requests
import time
from datetime import date
import random
import json
from tqdm import tqdm

from constants import API_KEY, API_KEY2, API_KEY3, API_KEY4

API_DICT = {
    'main': API_KEY,
    'aux1': API_KEY2,
    'aux2': API_KEY3,
    'aux3': API_KEY4
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


def getTrips(FC, SD, dataset, log_dest):
    '''
    Iterates over the BlaBlaCar trip endpoints.
    Checks for multiple page results, rotates keys and returns
    indexed results by department.

    - FC: From City, takes city row
    - SD: Starting Date, takes a datetime
    - dataset: Frame containing all possible destinations
    - log_dest: Takes a path to dump json results
    
    Returns
    -------
    :trips:

    '''
    trips = []

    local_dict = API_DICT

    for i, row in tqdm(dataset[~(dataset.index == FC.index[0])].iterrows()):

        local_dict = rotate(local_dict)
        KEY = local_dict['main']

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
            "from_coordinate": FC['coord'],
            "to_coordinate": row['coord'],
            "start_local_date": SD
        }

        querystring = dict(
            **QS_BASE
        )

        rj = None
        
        while rj is None:
            try:
                response = requests.request(
                    "GET",
                    URL,
                    headers=HEADERS,
                    params=querystring
                )
    
                rj = response.json()
    
                iterr_list.extend(rj['trips'])
    
                with open(log_dest, 'a') as f:
                    f.write(json.dumps(rj))
    
                while 'next_cursor' in rj:
    
                    time.sleep(random.uniform(1,2))
    
                    page = rj['next_cursor']
    
                    querystring = dict(
                        {'from_cursor': page},
                        **QS_BASE
                    )
    
                    response = requests.request(
                        "GET",
                        URL,
                        headers=HEADERS,
                        params=querystring
                    )
    
                    rj = response.json()
    
                    iterr_list.extend(rj['trips'])
    
                    with open(log_dest, 'a') as f:
                        f.write(json.dumps(rj))
    
                trips.append(
                    tuple([i, iterr_list])
                )

                time.sleep(
                    random.uniform(1, 3)
                )
    
            except ValueError as e:  # includes simplejson.decoder.JSONDecodeError
                print(f'Decoding JSON has failed for trips from {row.Commune}')
                with open(log_dest, 'a') as f:
                    f.write(e)
                    
                trips.append(tuple([i, None]))
    
            except KeyError as e:
                print(e, f'with KEY {KEY}. Remaining calls:', response.headers['x-ratelimit-remaining-day'])
                continue
                
            except ConnectionError as e:
                print(e)
                pass

    # print(f'Scraped trips from {FC.Commune}')

    return trips

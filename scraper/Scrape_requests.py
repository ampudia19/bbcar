import os
import time
import json
import random
from pathlib import Path
import pandas as pd
from datetime import date

# from multiprocessing.dummy import Pool as ThreadPool
import uuid
from concurrent.futures import ThreadPoolExecutor, ALL_COMPLETED, wait, as_completed
#%%
bbcardir = Path(os.environ['BLABLACAR_PATH'])
scriptsdir = bbcardir / 'git_scripts'
datadir = bbcardir / 'data'
outdir = bbcardir / 'output'
scrapedir = outdir / 'scraper'

os.chdir(scriptsdir / 'scraper')
today = date.today()

#%%
def uniquifier(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + "_" + str(counter) + extension
        counter += 1

    return path

def parser(file):
    '''
    Parses nested dictionaries into a dataframe, saves pickle.

    Parameters
    ----------
    file : dumped json list

    Returns
    -------
    output_df : trip dataframe

    '''
    with open(file) as f:
        data = json.loads(f.read())
           
    data = {k: v for x in data for k in x.keys() for v in x.values() if v['status']}
           
    trip_df = pd.DataFrame.from_dict(data, orient='index')
    
    t_list = []
    for i, row in trip_df.iterrows():
        try:
            rating_info = [item for sublist in row['rating'] for item in sublist]
        
            ride_df = pd.DataFrame([row['ride']], columns=row['ride'].keys())
            
            ride_df['ratings'] = [rating_info]
            
            ride_df = (
                ride_df
                .join(pd.json_normalize(ride_df['driver']).add_prefix('driver_'))
                .join(pd.json_normalize(ride_df['multimodal_id']))
                .join(pd.json_normalize(ride_df['vehicle']).add_prefix('vehicle_'))
                .join(pd.json_normalize(ride_df['seats']).add_prefix('seats_'))
            )
        
            t_list.append(ride_df)
                
        except Exception:
            # Skips deleted trips
            continue
        
        output_df = pd.concat(t_list)
        
        cols = [
            col
            for col in output_df.columns 
            if col.startswith('passengers') 
            or col.startswith('driver_')
            or col.startswith('vehicle_')
            or col.startswith('seats_')
            or col.startswith('ratings')
            ]
        
    output_df = (
        output_df[['id', 'comment', 'flags'] + cols]
        .rename(columns={'id': 'trip_id'})
    )
    
    output_df.reset_index(drop=True, inplace=True)
    
    return output_df

#%%
list_of_paths = scrapedir.glob('*.csv')
latest_path = max(list_of_paths, key=lambda p: p.stat().st_ctime) 

API_results = pd.read_csv(latest_path)

API_results = (
    API_results
    .dropna(subset=['trip_id'])
    .drop_duplicates(subset=['trip_id'])
    ['trip_id'].to_list()
)

file_to_operate = uniquifier(str(scrapedir / 'scrape_dumps' / f'{today}_trips.txt'))

#%% Call scraper from ScrapeSession module, dump JSON results
from ScrapeSession import ScrapeSession

trips_dict = {}
json_dump = []

while API_results:
    try:
        threads = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            for trip in API_results:
                threads.append(executor.submit(ScrapeSession().scrape, trip))
            for trip in as_completed(threads):
                json_dump.append(trip.result())
                
            wait(threads, timeout=7200, return_when=ALL_COMPLETED)
            # for trip in as_completed(threads)
            #     loop_list.append(tuple([trip, rj_trip['status']]))
                
            #     if rj_trip['status']:
            #         trip_dict[trip] = rj_trip
            
                
        merged_results = [x for i in threads for x in i.result().items()]
        merged_results = dict((x, y) for x, y in merged_results)
        
        trips_dict.update(merged_results)
     
        API_results = [x for x in trips_dict if not trips_dict[x]['status']]
    
    except Exception as e:
        print('########### ERROR THAT TERMINATES WHILE LOOP', e)
        # If crash, save results
        with open(file_to_operate, 'w') as f:
            f.write(json.dumps(json_dump))
            
# Dump results if trip id's are exhausted
with open(file_to_operate, 'w') as f:
            f.write(json.dumps(json_dump))        

#%% Parse JSON data

output_df = parser(file_to_operate)

output_df.to_pickle(outdir / 'scraper' / 'parsed_trips' / f'{today}_parsed_trip_results.pkl')

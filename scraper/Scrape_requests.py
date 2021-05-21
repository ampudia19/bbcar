import os
import time
import json
# import requests
# import csv  
import random
from pathlib import Path
import pandas as pd
from datetime import date
# import pickle

#%%
bbcardir = Path(os.environ['BLABLACAR_PATH'])
scriptsdir = bbcardir / 'git_scripts'
datadir = bbcardir / 'data'
outdir = bbcardir / 'output'
scrapedir = outdir / 'scraper'

os.chdir(scriptsdir / 'scraper')
today = date.today()

from ScrapeSession import ScrapeSession
#%%
def uniquifier(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + "_" + str(counter) + extension
        counter += 1

    return path

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
trip_dict = {}
loop_list = []

i = 0

while API_results:
    
    for trip in API_results:
        i += 1
        Scraper = ScrapeSession()
        
        rj_trip = Scraper.scrape(trip_id=trip)
        
        loop_list.append(tuple([trip, rj_trip['status']]))
        
        if rj_trip['status']:
            trip_dict[trip] = rj_trip
        
        if i % 25 == 0:
            try:
                with open(file_to_operate, 'w') as f:
                    f.write(json.dumps([trip_dict]))
                print('Saved at', i, 'over', len(API_results))
            except Exception as e:
                print('Error saving:', e)
                continue
    
        time.sleep(random.uniform(5,8))
        
    API_results = [x[0] for x in loop_list if not x[1]]


#%% Parse JSON data
# .replace('_1.txt', '.txt')
with open(file_to_operate) as f:
       data = json.loads(f.read())
       
trip_df = pd.DataFrame.from_dict(data[0], orient='index')

t_list = []
for i, row in trip_df.iterrows():
    try:
        rating_info = [item for sublist in row['rating'] for item in sublist]
    
        ride_df = (
            pd.DataFrame([row['ride']], columns=row['ride'].keys())
            # 
        )
        
        ride_df['ratings'] = [rating_info]
        
        ride_df = (
            ride_df
            .explode('passengers')
            .join(pd.json_normalize(ride_df['driver']).add_prefix('driver_'))
            .join(pd.json_normalize(ride_df['multimodal_id']))
            .join(pd.json_normalize(ride_df['vehicle']).add_prefix('vehicle_'))
            .join(pd.json_normalize(ride_df['seats']).add_prefix('seats_'))
        )
        
        ride_df = ride_df.reset_index(drop=True)
    
        try: # Captures passenger info, if any passengers
            ride_df = ride_df.join(pd.json_normalize(ride_df['passengers']).add_prefix('passenger_'))
        except:
            pass
    
        t_list.append(ride_df)
            
    except Exception:
        continue
    
    output_df = pd.concat(t_list)
    
    cols = [
        col
        for col in output_df.columns 
        if col.startswith('passenger_') 
        or col.startswith('driver_')
        or col.startswith('vehicle_')
        or col.startswith('seats_')
        ]
    
output_df = (
    output_df[['id', 'comment', 'flags'] + cols]
    .rename(columns={'id': 'trip_id'})
)

output_df.to_excel(outdir / 'scraper' / 'parsed_trips' / f'{today}_parsed_trip_results.xlsx')
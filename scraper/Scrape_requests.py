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
notebookdir = bbcardir / 'Notebooks'
datadir = bbcardir / 'data'
outdir = bbcardir / 'output'
scrapedir = outdir / 'scraper'

os.chdir(notebookdir / 'scraper')
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

API_results.dropna(subset=['trip_id'], inplace=True)

# API_results = API_results

file_to_operate = uniquifier(str(scrapedir / 'scrape_dumps' / f'{today}_trips.txt'))

#%% Call scraper from ScrapeSession module, dump JSON results
trip_dict = {}

for i, row in API_results.iterrows():
    
    Scraper = ScrapeSession()
    
    trip_dict[row['trip_id']] = Scraper.scrape(trip_id=row['trip_id'])
    trip_dict[row['trip_id']]['idx'] = str(i)
    
    # ha = list(trip_dict.items())[0][1]
    if i % 25 == 0:
        try:
            with open(file_to_operate, 'w') as f:
                f.write(json.dumps([trip_dict]))
        except:
            continue

    time.sleep(random.uniform(10,15))


#%% Parse JSON data

with open(file_to_operate.replace('_1.txt', '.txt')) as f:
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
    
output_df = output_df[['id', 'comment', 'flags'] + cols]

output_df.to_excel(outdir / 'scraper' / 'parsed_trips' / f'{today}_parsed_trip_results.xlsx')
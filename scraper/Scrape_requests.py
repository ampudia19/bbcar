import os
import json
from pathlib import Path
import pandas as pd
from datetime import date, datetime, timedelta
import time
import numpy as np

from concurrent.futures import ThreadPoolExecutor, ALL_COMPLETED, wait, as_completed
#%% Paths & times
bbcardir = Path(os.environ['BLABLACAR'])
scriptsdir = bbcardir / 'git_scripts'
datadir = bbcardir / 'data'
outdir = datadir / 'scraper' / 'output'
csvdir = datadir / 'scraper' / '_API_dumps' / 'csv'
os.chdir(scriptsdir / 'scraper')

now = datetime.now()
today = np.datetime64('today')
tomorrow = today + np.timedelta64(1, 'D')

dt_string = now.strftime("%Y%m%d_%H")

#%% Funs
def uniquifier(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + "_" + str(counter) + extension
        counter += 1

    return path

def parser(file):
    '''
    Parses nested dictionaries into a dataframe

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
        print(i)
        try:
            rating_info = [item for sublist in row['rating'] for item in sublist]
            
            ride_df = pd.DataFrame([row['ride']], columns=row['ride'].keys())
            
            ride_df['ratings'] = [rating_info]
            ride_df['web_scrape_time'] = row['web_scrape_time']
            
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
            pass
        
    output_df = pd.concat(t_list)
    
    print('made it')
    cols = [
        col
        for col in output_df.columns 
        if col.startswith('passengers') 
        or col.startswith('driver_')
        or col.startswith('vehicle_')
        or col.startswith('seats_')
        or col.startswith('ratings')
        or col.startswith('web_scrape')
        ]
    
    output_df = (
        output_df[['id', 'comment', 'flags'] + cols]
        .rename(columns={'id': 'trip_id'})
    )
    
    output_df.reset_index(drop=True, inplace=True)
    
    return output_df

file_to_operate = uniquifier(str(datadir / 'scraper' / '_scrape_dumps' / f'{today}_trips.txt'))

#%% Input list of trips to read and file to save on
list_of_paths = csvdir.glob('*.csv')
day_paths = [x for x in list_of_paths if str(today) in x.name]

# Load in data
lst_results = []
for item in day_paths:
    _ = pd.read_csv(item)
    lst_results.append(_)
results = pd.concat(lst_results)

# Define datetimes
results['start.date_time'] = pd.to_datetime(results['start.date_time'])
results['end.date_time'] = pd.to_datetime(results['end.date_time'])

# Preserve last time a trip is scraped in any of the 5 daily loops, while retaining information on the iteration at which it's scraped for the first time
API_results = (
    results
    .dropna(subset=['trip_id'])
    .sort_values(by=['num_id', 'day_counter'])
    .assign(iter_found=lambda df:
        df.groupby('num_id')['day_counter'].transform('min')
    )
    .drop_duplicates(subset=['num_id'], keep='last')
)

# Keep today-tomorrow trips
API_results = (
    API_results
    .loc[
        (API_results['start.date_time'].dt.date == today) |
        (API_results['start.date_time'].dt.date == tomorrow)
    ]
)

# Save unique matches for all trips
store_results = (
    results
    .dropna(subset=['trip_id'])
    .sort_values(by=['num_id', 'day_counter'])
    .drop_duplicates(subset=['num_id', 'DeptNum', 'destination'], keep='first')
)

store_results.to_csv(outdir / f'{dt_string}h_trips.csv')

# Create list to run web scraper through
API_results = API_results['trip_id'].to_list()

#%% Call scraper from ScrapeSession module, dump JSON results
from ScrapeSession import ScrapeSession

trips_dict = {}
json_dump = []

while API_results:
    try:
        base_len = len(API_results)
        threads = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for trip in API_results:
                threads.append(executor.submit(ScrapeSession().scrape, trip))
            for trip in as_completed(threads):
                json_dump.append(trip.result())

            wait(threads, timeout=7200, return_when=ALL_COMPLETED)

        merged_results = [x for i in threads for x in i.result().items()]
        merged_results = dict((x, y) for x, y in merged_results)

        trips_dict.update(merged_results)

        API_results = [x for x in trips_dict if not trips_dict[x]['status']]

        next_len = len(API_results)

        print(f'ITERATION COMPLETED. NEXT ITERATION HAS {next_len}, DOWN FROM {base_len} ORIGINAL TRIPS')

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

file_to_save = uniquifier(str(outdir / 'parsed_trips' / f'{today}_parsed_trip_results.pkl'))

output_df.to_pickle(file_to_save)

import os
import json
from pathlib import Path
import pandas as pd
from datetime import date, datetime
import time

from concurrent.futures import ThreadPoolExecutor, ALL_COMPLETED, wait, as_completed
#%% Paths & times
bbcardir = Path(os.environ['BLABLACAR_PATH'])
scriptsdir = bbcardir / 'git_scripts'
datadir = bbcardir / 'data'
outdir = datadir / 'scraper' / 'output'
csvdir = datadir / 'scraper' / '_API_dumps' / 'csv'
os.chdir(scriptsdir / 'scraper')

today = date.today()
now = datetime.now()
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
latest_paths = sorted(list_of_paths, key=lambda p: p.stat().st_ctime)[-5:]

lst_results = []

for item in latest_paths:
    iter_results = pd.read_csv(item)
    lst_results.append(iter_results)
results = pd.concat(lst_results)

# Drop preserves only first time a trip is scraped in any of the 5 daily loops
API_results = (
    results
    .dropna(subset=['trip_id'])
    .sort_values(by=['trip_id', 'day_counter'])
    .drop_duplicates(subset=['trip_id'], keep='first')
)

# Save unique matches for all trips
store_results = (
    results
    .dropna(subset=['trip_id'])
    .sort_values(by=['trip_id', 'day_counter'])
    .drop_duplicates(subset=['trip_id', 'DeptNum', 'destination'], keep='first')
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
        
        # Multithreading
        with ThreadPoolExecutor(max_workers=5) as executor:
            for trip in API_results:
                threads.append(executor.submit(ScrapeSession().scrape, trip))
            for trip in as_completed(threads):
                json_dump.append(trip.result())
                
            wait(threads, timeout=7200, return_when=ALL_COMPLETED)            
                
        # Build temp dictionary of results
        merged_results = [x for i in threads for x in i.result().items()]
        merged_results = dict((x, y) for x, y in merged_results)
        
        # Grow final dict
        trips_dict.update(merged_results)
        
        # Redefine trips to scrape if status is False
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

output_df.to_pickle(outdir / 'parsed_trips' / f'{today}_parsed_trip_results.pkl')

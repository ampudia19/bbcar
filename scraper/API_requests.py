"""
API_requests.
--------------
Maps the API functions on ori-dest pairs, processes data and stores it.

@author: David
"""

from datetime import datetime
from datetime import date
import os

from pathlib import Path
import pandas as pd

today = date.today()

#%% Paths
bbcardir = Path(os.environ["BLABLACAR"])
scriptsdir = bbcardir / 'git_scripts'
datadir = bbcardir / 'data'
outdir = datadir / 'scraper' / 'output'

os.chdir(scriptsdir / 'scraper')

from API_funs import getTrips, uniquifier

#%% Log and output files
log_dump = datadir / 'scraper' / '_API_dumps' / f'{today}_JSON.txt'
file_to_operate, day_counter = (
    uniquifier(
        str(datadir / 'scraper' / '_API_dumps' / 'csv' / f'{today}_trips.csv')
    )
)

#%% Process coord combination df
coordinate_mapper = pd.read_csv(
    datadir / 'scraper' / 'misc' / 'hotels-de-prefectures-fr.csv',
    sep=';'
)

coordinate_mapper = (
    coordinate_mapper.loc[
        (pd.to_numeric(coordinate_mapper['DeptNum'], errors='coerce').notnull()) &
        (pd.to_numeric(coordinate_mapper['DeptNum'], errors='coerce') < 100)
    ]
    .assign(
        Commune=lambda df:
            df['Commune'].str.normalize('NFKD')
            .str.encode('ascii', errors='ignore')
            .str.decode('utf-8'),
        coord=lambda df: df['LatDD'].round(4).astype(str) + ',' + df['LonDD'].round(4).astype(str),
        DeptNum=lambda df: df['DeptNum'].astype(int)
    )
    .set_index('DeptNum')
)
#%% Call in cities to request trips for
majors_df = (
    coordinate_mapper
    .loc[
        (coordinate_mapper.Commune == 'Paris') |
        (coordinate_mapper.Commune == 'Marseille') |
        (coordinate_mapper.Commune == 'Lyon') |
        (coordinate_mapper.Commune == 'Toulouse') |
        # (coordinate_mapper.Commune == 'Nimes') |
        (coordinate_mapper.Commune == 'Nice') |
        (coordinate_mapper.Commune == 'Rennes') |
        # (coordinate_mapper.Commune == 'Nantes') |
        (coordinate_mapper.Commune == 'Lille') |
        # (coordinate_mapper.Commune == 'Saint-Etienne') |
        (coordinate_mapper.Commune == 'Bordeaux') |
        (coordinate_mapper.Commune == 'Strasbourg') |
        (coordinate_mapper.Commune == 'Limoges')
    ]
    .copy()
)
# coordinate_mapper = coordinate_mapper.loc[coordinate_mapper.index==69]
#%% API calls
local_df = majors_df.copy()

trips_list = []

while not local_df.empty:
    for i, row in local_df.iterrows():
        try:
            results = getTrips(
                origin=row,
                startdate=today,
                dataset=coordinate_mapper,
                log_dest=log_dump
            )
            
            trips_list.append([i, results])
            local_df.drop(i, inplace=True)
        
        # Key error includes empty local_df. Break outside while loop
        except KeyError as e:
            print(e)
            break
        
        # If any other error, continues iterrows 
        except Exception as e:
            print(e)
            pass
    cur_length = local_df.shape[0]
    scraped_length = len(trips_list)
    
    print(f"TRIP LOOP COMPLETED: Retry {cur_length} trips. {scraped_length} trips have been scraped.")

API_results = pd.DataFrame(trips_list, columns=['DeptNum', 'results'])
API_results.set_index('DeptNum', inplace=True)

#%% Data Wrangling
majors_df = majors_df.merge(
    API_results,
    left_index=True,
    right_index=True,
    how='left'
)

# Split trips to different departments
results = (
    majors_df
    .copy()
    .explode('results')
)

# Split destination and trip information
results[['destination', 'API_scrape_time', 'trips']] = results['results'].apply(pd.Series)

# Explode json list data for individual blablacars
results = (
    results
    .drop(columns=['results'], axis=1)
    .explode('trips')
    .assign(trips=lambda df: df.trips.fillna({i: {} for i in results.index}))
    .reset_index()
)

# Flatten json individual trip data
results = results.join(pd.json_normalize(results['trips']))
results['trip_id'] = results.link.str.extract('id=(.*)')
results['waypoints'] = results.waypoints.fillna({i: [{}, {}] for i in results.index})

# Split and flatten start and endpoint information
results['start'] = [x[0] for x in results['waypoints']]
results['end'] = [x[1] for x in results['waypoints']]

results = results.join(pd.json_normalize(results['start'].tolist()).add_prefix("start."))
results = results.join(pd.json_normalize(results['end'].tolist()).add_prefix("end."))

# Extract actual trip identifier (numeric)
results['num_id'] = results.trip_id.str.extract('(\d+)')

results.drop(
    columns=[
        'Nom',
        'DeptNom',
        'LatDD',
        'LonDD',
        'trips',
        'waypoints',
        'start',
        'end'
    ],
    axis=1,
    inplace=True
)

results['day_counter'] = day_counter

results = results.sample(frac=1) #Shuffle

#%%
results.to_csv(file_to_operate)
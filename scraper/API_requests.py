# -*- coding: utf-8 -*-
"""
Created on Tue May  4 13:11:55 2021

@author: David
"""

from datetime import datetime
from datetime import date
import os

from pathlib import Path
import pandas as pd

#%%
bbcardir = Path(os.environ["BLABLACAR_PATH"])
scriptsdir = bbcardir / 'git_scripts'
datadir = bbcardir / 'data'
outdir = datadir / 'scraper' / 'output'

os.chdir(scriptsdir / 'scraper')

from API_funs import getTrips

#%%

today = date.today()

log_dump = datadir / 'scraper' / '_API_dumps' / f'{today}_JSON.txt'

#%%
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
#%%
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
        # (coordinate_mapper.Commune == 'Orleans') |
        # (coordinate_mapper.Commune == 'Nantes') |
        (coordinate_mapper.Commune == 'Lille') |
        # (coordinate_mapper.Commune == 'Saint-Etienne') |
        (coordinate_mapper.Commune == 'Bordeaux') |
        (coordinate_mapper.Commune == 'Strasbourg')
        # (coordinate_mapper.Commune == 'Limoges')
    ]
)

#%%
majors_df = majors_df.copy()

majors_df['results'] = majors_df.apply(
    lambda row: getTrips(
        FC=row,
        SD=today,
        dataset=coordinate_mapper,
        log_dest=log_dump), 
    axis=1
)

#%%
# Split trips to different departments
results = (
    majors_df
    .copy()
    .explode('results')
)

# Split destination and trip information
results[['destination', 'trips']] = results['results'].apply(pd.Series)

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

results.sample(frac=1) #Shuffle

#%%
now = datetime.now()

dt_string = now.strftime("%Y%m%d_%H")

results.to_csv(outdir / f'{dt_string}h_trips.csv')
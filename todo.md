# To do's

- :wrench: fix: Move API key rotation outside funs. Otherwise we can't scape running out of daily requests.
	- Alternatively, reduce # of trips scraped a day.
- :construction: feat: Implement multithreading for API requests.
- :construction: feat: Integrate visual recognition software

- :apple: chore: reduce time it takes for loop to complete: constaint to same-day trips in webscrape. 
	- It currently captures trips as many as three days ahead of today date.

- :apple: chore: take DICT outside funs so that expended keys are popped permantently.
- :apple: chore: fix five-file that is loaded for scraper using date. 


### talk 5pm
- trip API check 2h mismatch
- price may change until first passenger books. 

### tasks
- passengers appear chronologically
- manual looking at a ori-dest pair, check later and validate that any additions in API were not observed in the browser
- 2h mismatch → manually set up trips, run API, test time-to-upload
- facial recognition manually code, check for model accuracy
- day_counter → take last instead, to obtain as-updated-as-possible snaps of trips. 

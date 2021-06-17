# To do's

- :wrench: fix: Move API key rotation outside funs. Otherwise we can't scape running out of daily requests.
		- Alternatively, reduce # of trips scraped a day.
- :construction: feat: Implement multithreading for API requests.
- :construction: feat: Integrate visual recognition software

- :apple: chore: reduce time it takes for loop to complete: constaint to same-day trips in webscrape. 
		- It currently captures trips as many as three days ahead of today date.

- :apple: chore: take DICT outside funs so that expended keys are popped permantently.
- :apple: chore: fix five-file that is loaded for scraper using date. 
# To do's

- [x] :wrench: fix: Move API key rotation outside funs. Otherwise we can't scape running out of daily requests.
	- Alternatively, reduce # of trips scraped a day.
	- Solution: Random picks instead.
- :construction: feat: Implement multithreading for API requests.
- :construction: feat: Integrate visual recognition software

- :apple: chore: reduce time it takes for loop to complete: constrain to same-day trips in webscrape. 
	- It currently captures trips as many as three days ahead of today date.

- [x] :apple: chore: fix five-file that is loaded for scraper using date. 


### talk 5pm
- [x] trip API check 2h mismatch
- [ ] price may change until first passenger books. 
	- Of what use is this?

### tasks
- [x] passengers appear chronologically
	- confirmed with subset of Paris-to-Lyon trips, new passengers are appended at bottom of json list. 
- [x] manual looking at a ori-dest pair, check later and validate that any additions in API were not observed in the browser
	- If no more passengers, trip no longer returned. Possibility of misclassification. 
	- https://www.blablacar.fr/trip?source=CARPOOLING&id=2208359478-antony-saint-priest no longer returned, but still available for booking.
	- https://www.blablacar.fr/trip?source=CARPOOLING&id=2208359478-antony-villeurbanne found as new (misclass?). Kinda. Numeric ID constant, can filter out those. 
	- https://www.blablacar.fr/trip?source=CARPOOLING&id=2208359478-antony-lyon
		- [x] :construction: feat: create id numeric column, re-label approx. trips if ID same but dest. diff. 
	- Otherwise deleted, no seats, departed.
- [x] 2h mismatch → manually set up trips, run API, test time-to-upload
- [ ] facial recognition manually code, check for model accuracy
	- [x] download thumbnails
	- [ ] pass through algorithm
- [x] day_counter → take last instead, to obtain as-updated-as-possible snaps of trips. 

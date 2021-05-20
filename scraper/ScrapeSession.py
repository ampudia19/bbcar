import time
import sys
import json
import logging
import requests
from datetime import date
import random
# from fake_useragent import UserAgent

from pathlib import Path

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

today = date.today()

#%%
MESSAGE_INFO = "%(asctime)s %(trip)s ----- %(message)s"
DATEFMT = "%Y/%m/%d %H:%M"

file_handler = logging.FileHandler(
    filename=f'./log/trip/{today}_scraper.log', 
    mode='a'
)

file_handler.setFormatter(
    logging.Formatter(
        fmt=MESSAGE_INFO,
        datefmt=DATEFMT
    )
)

stream_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format=MESSAGE_INFO,
    datefmt=DATEFMT,
    handlers=[
        file_handler,
        stream_handler
    ]
)

class ScrapeSession(object):
    _BASE_URL = "https://www.blablacar.co.uk"
    # USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 OPR/76.0.4017.107"
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # ua = UserAgent()
        # USER_AGENT = str(self.ua.random)
        
        self._create_session()
        
    @staticmethod
    def _super_proxy():
        return '142.54.160.122:19020'

    def _create_session(self):
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en_GB",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
        
        self.session = requests.session()
        self.session.headers = headers
        self.session.verify = False
        proxy = self._super_proxy()
        self.session.proxies = {
            'http': proxy,
            'https': proxy,
        }
        while True:
            try:
                self.session.get(self._BASE_URL, timeout=10)
                break
            except Exception as e:
                print('ERROR AT SETTING SESSION:', e)
                time.sleep(30)
                continue
        
    def scrape(self, trip_id):
        '''
        Parses JSON results from trip-specific Blablacar page. Returns 
            - Name of driver
            - Description
            - Passenger' names
            - Driver reviews
        
        Returns
        -------
        :param trip_id:
        :return:
            
        '''
        trip_info = {'trip': trip_id}
        self._logger = logging.LoggerAdapter(self._logger, trip_info)
        
        result = {
            "ride": {},
            "rating": []
        }

        data = {
            "source": "CARPOOLING",
            "id": trip_id,
        }
        
        i = 0
        
        while True:    
            try:
                i+=1
                self._logger.info('CREATE SESSION')
                # self._create_session()
                
                # return self.session
                # break
            
                if i >= 4:
                    self._logger.info('SKIPPED REQUEST')
                    return {'ride': False}
                    break
                
                time.sleep(random.uniform(4,6))
                self._logger.info('REQUESTING INFO')
                
                repeat = None
                
                response = self.session.get(
                    "{}/trip".format(self._BASE_URL),
                    params=data,
                    timeout=30
                )
                
                if response.status_code == 403: # Not an exception
                    self._logger.info(f'403 FORBIDDEN ERROR: {response.reason}')
                    time.sleep(random.uniform(4,6))
                    if i >= 2:
                        self._logger.info('SKIPPED REQUEST')
                        time.sleep(random.uniform(15,20))
                        return {'ride': False}
                        break
                    continue
                
                if response.status_code == 502: # Not an exception
                    self._logger.info(f'502 BAD GATEWAY: {response.reason}')
                    time.sleep(random.uniform(5, 40))
                    if i >= 2:
                        self._logger.info('SKIPPED REQUEST')
                        return {'ride': False}
                        break
                    continue
                    
                else:
                    time.sleep(random.uniform(4,6))
                    
                    #-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+##-+#-+#-+#-+
                    self._logger.info('REQUESTING TRIP DETAILS')
                    self.session.headers = {
                        "User-Agent": self.USER_AGENT,
                        "Accept": "application/json",
                        "Accept-Language": "en_GB",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Referer": str(self._BASE_URL +'/'),
                        "Content-Type": "application/json",
                        'sec-ch-ua-mobile': '?0', #
                        'sec-fetch-dest': 'empty', #
                        'sec-fetch-mode': 'cors', #
                        'sec-fetch-site': 'same-site', #
                        "X-Blablacar-Accept-Endpoint-Version": "4", # 5
                        "x-locale": "en_GB",
                        "x-visitor-id": self.session.cookies['vstr_id'],
                        "x-currency": "GBP",
                        # "x-correlation-id": "ecffc2e4-1adf-4ce1-be44-9493a4c42504",
                        "x-client": "SPA|1.0.0",
                        "x-forwarded-proto": "https",
                        "Authorization": f"Bearer {self.session.cookies['app_token']}",
                        "Origin": "https://www.blablacar.co.uk",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Pragma": "no-cache",
                        "Cache-Control": "no-cache",
                        "TE": "Trailers"
                    }
                    
                    data = {
                        "source": "CARPOOLING",
                        "id": trip_id,
                        "requested_seats": "1",
                    }
                    
                    response = self.session.get(
                        "https://edge.blablacar.co.uk/ride",
                        params=data,
                        timeout=30
                    )
                    
                    # return self.session
                    # break
                    if response.status_code == 404: # Not an exception
                        self._logger.info(f'TRIP DELETED: {response.reason}')
                        time.sleep(random.uniform(2,3))
                        return {'ride': False}
                        break
            
                    if not response.ok:
                        self._logger.info("FAULT AT SECOND REQUEST: {} {}".format(response.status_code, response.reason))
                        repeat = True
            
                    ride = response.json()
                    result['ride'] = ride
                    
                    time.sleep(random.uniform(4,6))
                    
                    #-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+#-+##-+#-+#-+#-+
                    self._logger.info('REQUESTING RATINGS')
                    
                    page_num = 0
                    total_pages = 1
                    
                    while page_num < total_pages:
                        page_num += 1
                        data = {
                            "page": page_num,
                            "limit": "100",
                        }
                        
                        response = self.session.get(
                            "https://edge.blablacar.co.uk/api/v2/users/{}/rating".format(ride['driver']['id']),
                            params=data,
                            timeout=30
                        )
                        
                        if not response.ok:
                            self._logger.info("FAULT AT THIRD REQUEST: {} {}".format(response.status_code, response.reason))
                            repeat = True
                    
                        ratings_data = response.json()
                        
                        try:
                            result['rating'].append(ratings_data['ratings'])
            
                            total_pages = ratings_data['pager'].get('pages', total_pages)
                        
                            time.sleep(random.uniform(4,10))
                        
                            self._logger.info('RATINGS PAGE %s' % page_num)
                        
                        except KeyError:
                            self._logger.info("NO RATINGS")
                            result['rating'] = ['No Ratings']
                    
                    if repeat == None: # End loop
                        self._logger.info('<<<FINISHED SCRAPE>>>')
                        break
                
            except Exception as e:
                self._logger.info("REQUEST ERROR: {}".format(e))
                time.sleep(random.uniform(5,10))
                continue
        
        return result
    
#%%
if __name__ == '__main__':
    scrape_session = ScrapeSession()
    


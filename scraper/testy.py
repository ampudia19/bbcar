# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 17:26:34 2021

@author: u82929
"""

import time
import logging
import requests
from datetime import date
import random

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

today = date.today()

# %%

_BASE_URL = "https://www.blablacar.fr"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 OPR/76.0.4017.107"
    

headers = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

def _super_proxy():
    proxies = [
        '51.15.2.163:19017',
        '163.172.36.215:19002',
        '62.210.205.97:19017',
        '163.172.214.121:19012',
        '163.172.213.213:19003',
        '51.15.1.31:19006',
        '163.172.214.121:19003',
        '163.172.161.185:19005',
        '51.15.1.31:19003',
        '51.15.2.105:19015'
    ]
    
    pick = random.choice(proxies)
    return pick

# %%
for i in range(1,21):
    session = requests.session()
    session.headers = headers
    session.verify = False
    proxy = _super_proxy()
    session.proxies = {
                'http': proxy,
                'https': proxy,
    }
    
    l = session.get(_BASE_URL, timeout=10)
    print(proxy, l)
    time.sleep(random.uniform(2,4))

time.sleep(random.uniform(2,3))
trip_id = '2320621693-toulouse-marssac-sur-tarn'
trip_info = {'trip': trip_id}

result = {
    trip_id: {
        "ride": {},
        "rating": [],
        "status": None
    }
}

data = {
    "source": "CARPOOLING",
    "id": trip_id,
}

response = session.get(
                    "{}/trip".format(_BASE_URL),
                    params=data,
                    timeout=30
                )
time.sleep(random.uniform(2,3))

session.headers = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "fr_FR",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": str(_BASE_URL +'/'),
    "Content-Type": "application/json",
    'sec-ch-ua-mobile': '?0', #
    'sec-fetch-dest': 'empty', #
    'sec-fetch-mode': 'cors', #
    'sec-fetch-site': 'same-site', #
    "X-Blablacar-Accept-Endpoint-Version": "4", # 5
    "x-locale": "fr_FR",
    "x-visitor-id": session.cookies['vstr_id'],
    "x-currency": "EUR",
    "x-client": "SPA|1.0.0",
    "x-forwarded-proto": "https",
    "Authorization": f"Bearer {session.cookies['app_token']}",
    "Origin": "https://www.blablacar.fr",
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
print(response)
time.sleep(random.uniform(4,5))
response = session.get(
    "https://edge.blablacar.fr/ride",
    params=data,
    timeout=30
)

# %%
ride = response.json()

# %% 

from bs4 import BeautifulSoup
proxy = _super_proxy()
tryng = requests.get("https://whatthefuckismyip.net",
                     proxies = {
            'http': proxy,
          'https': proxy,
}
)         
print(tryng.text.split()[-1])


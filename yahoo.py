import pandas as pd 
import datetime, requests, os, keyboard
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
from sys import exit
from plyer import notification

def web_content_div(web_content, class_path, value):
    web_content_div = web_content.find_all('div', {'class': class_path})
    try:
        if value != 'None':
            spans = web_content_div[0].find_all(value)
            texts = [span.get_text() for span in spans]
        else:
            texts = []
    except IndexError:
        texts = []

    return texts

def real_time_price(ticker):
    Error = 0
    url = 'https://finance.yahoo.com/quote/' + ticker + '?p=' + ticker + '&.tsrc=fin-srch'
    try:
        r = requests.get(url)
        web_content = BeautifulSoup(r.text, 'lxml')
        texts = web_content_div(web_content, 'D(ib) Mend(20px)', 'fin-streamer')
        price, change, volume, latest_pattern, one_year_target = [], [], [], [], []

        if texts != []:
            price, change = texts[0], texts[1] + ' ' + texts[2]
        else:
            Error = 1
            price, change = [], []
        
        if ticker[-2:] == '=F':
            texts = web_content_div(web_content, 'D(ib) W(1/2) Bxz(bb) Pstart(12px) Va(t) ie-7_D(i) ie-7_Pos(a) smartphone_D(b) smartphone_W(100%) smartphone_Pstart(0px) smartphone_BdB smartphone_Bdc($seperatorColor)'
                                    , 'fin-streamer')
        else:
            texts = web_content_div(web_content, 'D(ib) W(1/2) Bxz(bb) Pend(12px) Va(t) ie-7_D(i) smartphone_D(b) smartphone_W(100%) smartphone_Pend(0px) smartphone_BdY smartphone_Bdc($seperatorColor)'
                                    , 'fin-streamer')
            
        if texts != []: 
            volume = texts[0]
        else:
            Error = 1
            volume = []
        
    except ConnectionError:
        price, change, volume, latest_pattern, one_year_target = [], [], [], [], []
        Error = 1
        print('Connection Eror')

    return price, change, volume, latest_pattern, one_year_target, Error

tickers = ['AAPL']

while True:   
    for ticker in tickers:
        price, change, volume, latest_pattern, one_year_target, Error = real_time_price(ticker)
        print(ticker)
        print(f'price: {price}')
        print(f'change: {change}')
        print(f'volume: {volume}')
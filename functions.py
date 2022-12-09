from secrets import *
from config import *

from datetime import datetime
import requests
# import random
from lxml.html import fromstring
from lxml import html
import json
import lxml

def send_telegram_message(message: str,
                          chat_id: str = TG_CHAT_ID,
                          api_key: str = TG_API_KEY,
                          proxy_username: str = None,
                          proxy_password: str = None,
                          proxy_url: str = None):
    responses = {}

    proxies = None
    if proxy_url is not None:
        proxies = {
            'https': f'http://{username}:{password}@{proxy_url}',
            'http': f'http://{username}:{password}@{proxy_url}'
        }
    headers = {'Content-Type': 'application/json',
               'Proxy-Authorization': 'Basic base64'}
    data_dict = {'chat_id': chat_id,
                 'text': message,
                 'parse_mode': 'HTML',
                 'disable_notification': True}
    data = json.dumps(data_dict)
    url = f'https://api.telegram.org/bot{api_key}/sendMessage'
    response = requests.post(url,
                             data=data,
                             headers=headers,
                             proxies=proxies,
                             verify=False)
    return response

def print_log_message(text):
    print('[{}]: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), text))

# https://www.scrapehero.com/how-to-rotate-proxies-and-ip-addresses-using-python-3/
def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr'):
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

PROXY = ''
def choose_new_proxy(proxies):
    if len(proxies) < 2:
        proxies += get_proxies()

    PROXY = proxies.pop(0)
    print_log_message('Новый адрес прокси:\t{}. Осталось:\t{} адресов (при обнулении, автоматически загрузятся новые)'.format(PROXY, len(proxies)))

    return PROXY

def get_data(proxy = ''):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
    }

    print_log_message('Словарь параметров прокси:')
    print_log_message({"http": proxy, "https": proxy})
    response = requests.get(
        PAGE_URL,
        headers=headers,
        proxies={"http": proxy, "https": proxy}
    )
    
    print_log_message('Статус ответа: {}'.format(response.status_code))
    if response.status_code != 200:
        return {
            'matches': [],
            'status_code': response.status_code
        }
    
    tree = fromstring(response.content) 
    phases = list(
        tree
        .xpath('//*[@class="performances_sub_container performances_monthly_grouped performances_monthly_sold_out performances_grouped_by_phase"]')
        #.xpath('//*[contains(@class, "performances_sub_container performances_monthly_grouped")]')
    ) + list(
        tree
        .xpath('//*[@class="performances_sub_container performances_monthly_grouped performances_grouped_by_phase"]')
    )
    print(phases)
    
    print_log_message('Вижу {} фаз. Пробую извлечь данные о матчах...'.format(len(phases)))
    matches_data = []
    for phase in phases:
        matches = phase.find_class('perf_details')
        for match in matches:
            match_data = {'phase': phase.xpath('div/h3')[0].text}

            match_data['match_round_code'] = (
                match
                .find_class('match_round_code perf_info_list_content')[0]
                .text
            )

            match_data['match_date_time'] = (
                match
                .find_class('date_time perf_info_list_element')[0]
                .text_content()
                .strip().replace('\t', '').replace('\r\n', ' ')
            )

            match_data['match_stadium'] = (
                match
                .find_class('semantic-no-styling venue_group_match perf_info_list_element')[0]
                .find_class('site')[0]
                .text
            )

            match_data['match_team_home'] = (
                match
                .find_class('team home')[0]
                .find_class('name')[0]
                .text
            )

            match_data['match_team_opposite'] = (
                match
                .find_class('team opposite')[0]
                .find_class('name')[0]
                .text
            )

            if len(match.find_class('buttons_availability resale perf_info_list_element last_element align_right')[0].find_class('from sold_out_text')) != 0:
                match_data['match_status'] = (
                    match
                    .find_class('buttons_availability resale perf_info_list_element last_element align_right')[0]
                    .find_class('from sold_out_text')[0]
                    .text
                )
            else:
                match_data['match_status'] = 'UNKNOWN'

            matches_data.append(match_data)
    
    print_log_message('Собрали информацию о {} матчах.'.format(len(matches_data)))
    for element in matches_data:
        for key in element:
            print(key, ':', element[key])
        print()
    return {
            'matches': matches_data,
            'status_code': response.status_code
        }
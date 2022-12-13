import logging

from secrets import TG_CHAT_ID, TG_API_KEY
from config import PAGE_URL, USER_AGENT, REQUEST_TIMEOUT_SEC

import requests
from lxml.html import fromstring
import json


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
            'https': f'https://{proxy_username}:{proxy_password}@{proxy_url}',
            'http': f'http://{proxy_username}:{proxy_password}@{proxy_url}'
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


def get_proxies():
    """
    The function gets a list of free proxies from the site free-proxy-list.net
    """
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr'):
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            # Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return list(proxies)


def choose_new_proxy(proxies: list):
    """
    The function selects one proxy. If the proxy list has ended, it requests a new proxy list.
    """
    if not len(proxies):
        proxies = get_proxies()

    proxy = proxies.pop(0)
    logging.info(
        f'New proxy:\t{proxy}. We have:\t{len(proxies)} proxy addresses left. ' +
        '(when the proxies run out, new ones will automatically load)'
    )

    return [proxy, proxies]


def get_data(proxy: str):
    """
    Get and parse data from website
    """
    headers = {
        'user-agent': USER_AGENT,
    }

    logging.info(f'Current proxy:\t{proxy}')
    response = requests.get(
        PAGE_URL,
        headers=headers,
        proxies={"http": proxy, "https": proxy},
        timeout=REQUEST_TIMEOUT_SEC
    )

    if response.status_code != 200:
        response.raise_for_status()

    tree = fromstring(response.content)
    phases = list(
        tree
        .xpath(
            '//*[@class="performances_sub_container performances_monthly_grouped performances_monthly_sold_out performances_grouped_by_phase"]')
    ) + list(
        tree
        .xpath('//*[@class="performances_sub_container performances_monthly_grouped performances_grouped_by_phase"]')
    )

    logging.debug(f'I see {len(phases)} phases. I\'m trying to extract match data...')
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

            if len(match.find_class('buttons_availability resale perf_info_list_element last_element align_right')[
                       0].find_class('from sold_out_text')) != 0:
                match_data['match_status'] = (
                    match
                    .find_class('buttons_availability resale perf_info_list_element last_element align_right')[0]
                    .find_class('from sold_out_text')[0]
                    .text
                )
            else:
                match_data['match_status'] = 'UNKNOWN'

            matches_data.append(match_data)

        debug_text = f'Collected information about {len(matches_data)} matches.\n'
        for element in matches_data:
            for key in element:
                debug_text += f'{key}:{element[key]}\n'
            debug_text += '\n'
        logging.debug(debug_text)

    return matches_data

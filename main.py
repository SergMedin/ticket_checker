import logging

from config import TG_NOTIFICATIONS, DELAY_SEC, COUNTER_LIMIT, proxies
from functions import send_telegram_message, choose_new_proxy, get_data

from time import sleep
from requests.exceptions import HTTPError, SSLError, ProxyError, ConnectTimeout, ConnectionError
from lxml.etree import ParserError

# try level=logging.DEBUG if you need more information
logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')


def main(proxies: list):
    logging.info('We are trying to get a list of proxies...')
    proxy, proxies = choose_new_proxy(proxies)

    counter = -1
    while True:
        counter += 1
        logging.info('')
        while True:
            try:
                logging.info('We are trying to get data from the site...')
                data = get_data(proxy)
                break
            except (HTTPError, SSLError, ProxyError, ConnectTimeout, ConnectionError, ParserError) as error:
                logging.error(error)
                proxy, proxies = choose_new_proxy(proxies)
                logging.info('Fall asleep for 1 second')
                sleep(1)

        tickets_found = False
        logging.info('Data from the site has been received. We check if there are tickets...')
        for match in data:
            if match['match_status'] != 'Currently unavailable':
                logging.info('There are tickets! :)')
                tickets_found = True
                counter = -1  # as soon as the tickets disappear, we will receive a notification that they are not there

                message = 'It looks like there are tickets for at least this match:\n'
                for key in match:
                    message += f'{key}: {match[key]}\n'

                if TG_NOTIFICATIONS:
                    send_telegram_message(message)

                # we fall asleep for a long time
                sleeping_delay_sec = DELAY_SEC * 10
                logging.info(f'Falling asleep for {sleeping_delay_sec} seconds')
                sleep(sleeping_delay_sec)
                break

        if not tickets_found:
            logging.info('There are no tickets! :(')
            if counter == 0 or counter > COUNTER_LIMIT:
                if TG_NOTIFICATIONS:
                    # Just notify that the bot is working
                    send_telegram_message('There are no tickets. But I\'m alive and well :)')
                counter = 0

            logging.info(f'Fall asleep for {DELAY_SEC} seconds')
            sleep(DELAY_SEC)


if __name__ == '__main__':
    main(proxies)

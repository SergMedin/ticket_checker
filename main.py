from time import sleep

# from config import *
# from secrets import *
from functions import *

print_log_message('Пробуем получить список прокси...')
proxies = []
proxy = choose_new_proxy(proxies)

counter = -1
while True:
    counter += 1
    print_log_message('')
    while True:
        try:
            print_log_message('Пробуем получить данные с сайта...')
            data = get_data(proxy)
            break
        except requests.exceptions.SSLError:
            print_log_message('requests.exceptions.SSLError')
            proxy = choose_new_proxy(proxies)
        except requests.exceptions.ProxyError:
            print_log_message('requests.exceptions.ProxyError')
            proxy = choose_new_proxy(proxies)
        except lxml.etree.ParserError:
            print_log_message('lxml.etree.ParserError')
            proxy = choose_new_proxy(proxies)
        
    if data['status_code'] != 200:
        print_log_message('Данные сайта не получены. Попробуем поменять прокси. Статус: {}'.format(data['status_code']))
        proxy = choose_new_proxy(proxies)
        print_log_message('Засыпаем на 1 секунду')
        sleep(1)
        continue
    
    no_tickets = True
    print_log_message('Данные с сайта получены. Проверяем есть ли билеты...')
    for match in data['matches']:
        if match['match_status'] != 'Currently unavailable':
            print_log_message('Уведомляем, что есть билеты')
            no_tickets = False
            
            message = 'Похоже, есть билеты, как минимум на этот матч:\n'
            for key in match:
                message += key + ': ' + match[key] + '\n'
                
            if TG_NOTIFICATIONS:
                send_telegram_message(message)
            
            # засыпаем надолго
            print_log_message('Засыпаем на {} секунд'.format(DELAY_SEC*20))
            sleep(DELAY_SEC*20)
            break
            
    if no_tickets:
        if counter == 0 or counter > COUNTER_LIMIT:
            print_log_message('Билетов нет')
            if TG_NOTIFICATIONS:
                send_telegram_message('Билетов нет. Но я жив, здоров :)')
            counter = 0

        print_log_message('Засыпаем на {} секунд'.format(DELAY_SEC))
        sleep(DELAY_SEC)
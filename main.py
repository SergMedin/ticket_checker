from time import sleep

# from config import *
# from secrets import *
from functions import *

print_log_message('Пробуем получить список прокси...')
proxies = []
choose_new_proxy(proxies)

counter = -1
while True:
    counter += 1
    print_log_message('')
    print_log_message('Пробуем получить данные с сайта...')
    data = get_data()
    if data['status_code'] != 200:
        print_log_message('Данные сайта не получены. Попробуем поменять прокси. Статус: {}'.format(data['status_code']))
        choose_new_proxy(proxies)
        continue
     
    print_log_message('Данные с сайта получены. Проверяем есть ли билеты...')
    for match in data['matches']:
        if match['match_status'] != 'Currently unavailable':
            print_log_message('Уведомляем, что есть билеты')
            
            message = 'Похоже, есть билеты, как минимум на этот матч:\n'
            match = tmp['matches'][0]
            for key in match:
                message += key + ': ' + match[key] + '\n'
            send_telegram_message(message)
            
            # засыпаем надолго
            sleep(DELAY_SEC*10)
            break
    print_log_message('Билетов нет')
    
    if counter == 0 or counter > COUNTER_LIMIT:
        send_telegram_message('Билетов нет. Но я жив, здоров :)')
        counter = 0
    
    sleep(DELAY_SEC)
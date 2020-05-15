
import argparse
import logging
import sys
import os
import requests
import configparser

from openpyxl import load_workbook


# Опрдеделяем файл для логирования
logging.basicConfig(filename='add_vacancy.log',
                    filemode='w', level=logging.DEBUG)



# Получаем данные из файла конфигурации
config = configparser.RawConfigParser()
try:
    config.read('config.txt')
    dict_config = dict(config.items('API_CONFIG'))
    endpoint = dict_config["endpoint"]
    accounts_id = dict_config["accounts_id"]
    get_status = dict_config["get_status"]
    get_list_vacancy = dict_config["get_list_vacancy"]
    post_add_in_base = dict_config["post_add_in_base"]
    post_add_on_vacancy = dict_config["post_add_on_vacancy"]
    get_all_applicants = dict_config["get_all_applicants"]
    post_upload_file = dict_config["post_upload_file"]

except Exception:
    logging.exception('Ошибка при чтении файла конфигурации')
    raise Exception('Ошибка при чтении файла конфигурации')


def pars_arg(args):
    '''Определяем необходимые аргументы для работы скрипта
    '''
    parser = argparse.ArgumentParser(
        description='Необходим токен и путь к базе')
    parser.add_argument(
        '--token',
        required=True,
        dest="token",
        help='Необходимо ввести токен ')
    parser.add_argument(
        '--path',
        required=True,
        dest="path",
        help='Путь до директории с файлами')

    parser.add_argument(
        '-n',
        dest="number_to_continue",
        default=0,
        type=int,
        help='номер записи для продолжения в случае ошибки(Не обязательно)')
    return parser.parse_args(args)


# Склеиваю url. Знаю что есть urljoin, но так как я часто передаю более двух аргументов
# проще было написать свою.
def joinurl(*args):
    return "/".join(map(lambda x: str(x).rstrip('/'), args))


def get_account_id(url, headers):
    ''' Получаем account_id для использования в запросах

    Передаем url, headers
    Получаем items из базы проверяем сколько там записей организаций,
    обрабатываем и получаем нужный нам id
    '''
    result = requests.get(url, headers=headers).json()
    if len(result['items']) > 1:
        print('Выбирете организацию')
        for i, el in enumerate(result['items']):
            print(f'{i+1}--{el["name"]}')

        while True:
            try:
                i = int(input('Введите номер организации или 0 для выхода\n'))
            except NameError:
                continue
            if i == 0:
                return -1
            else:
                try:
                    id == result['items'][i-1]['id']
                    return id
                except IndexError:
                    continue
                except Exception:
                    return -1

    elif len(result['items']) == 1:
        return result['items'][0]['id']
    else:
        logging.exception('Ошибка при получении id')
        raise Exception('Ошибка при получении id')


def get_vacancies_id(full_endpoint, headers):
    '''Получаем id вакансий'''
    dict_id_vacancy = {}
    r = requests.get(
        joinurl(full_endpoint, get_list_vacancy), headers=headers)
    for item in r.json()['items']:
        dict_id_vacancy[item['position']] = item['id']

    logging.debug(f'Получили список вакансий {dict_id_vacancy}')
    return dict_id_vacancy


def get_status_id(full_endpoint, headers):
    ''' Получаем статусы и их id'''
    dict_id_status = {}
    r = requests.get(joinurl(full_endpoint, get_status), headers=headers)
    for item in r.json()['items']:
        dict_id_status[item['name']] = item['id']
    logging.debug(f'Получили список статусов {dict_id_status}')
    return dict_id_status


def upload_files(fio, position, path_to_base, token, full_endpoint):
    ''' Ищем резюме конкретного кандидата и загружаем на сервер. Получаем id загруженных файлов'''

    dir_files_resume = os.listdir(os.path.join(path_to_base, position))
    headers = {'Content-Type': 'multipart/form-data',
               'Authorization': f'Bearer {token}',
               'X-File-Parse': 'true',
               'user-agent': 'App/1.0',
               }
    try:
        multiple_files = []
        for f in dir_files_resume:
            if f.startswith(fio.strip()):
                url = joinurl(full_endpoint, post_upload_file)
                fileobj = open(os.path.join(path_to_base, position, f), 'rb')
                files = {"file":  fileobj}
                print(f'Найдены подходящие резюме {f}')
                r = requests.post(url, headers=headers, files=files)
                multiple_files.append(r.json()['id'])
        logging.debug(f'получили id файлов{multiple_files}')
        print('Резюме загружено')

    except Exception as e:
        print('Резюме не загружено ')
        logging.exception(e)

    return multiple_files

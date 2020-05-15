from help_utilts import *


def _get_data_from_row_xls(row):
    '''Функция для обработки строк xlsx файла и приведение данных к нужному формату
    Возвращает словарь с данными и поле с коментарием. Используется в parse_xls
     '''
    print(row[1])
    applicants = {}
    applicants['position'] = row[0].strip()
    FIO = row[1].strip().split()
    if len(FIO) < 2:
        print('Нет имени или фамилии для кандидата')
        raise Exception("Нет имени или фамилии для кандидата")
    else:
        applicants['last_name'] = FIO[0]
        applicants['first_name'] = FIO[1]
        try:
            applicants['midle_name'] = FIO[2]
        except:
            pass
    money = str(row[2])
    try:
        applicants['money'] = str(int(float(money)))+' руб'
    except Exception as e:
        logging.exception(e)
        applicants['money'] = "".join(
            [s for s in money.split() if s.isdigit()])+' руб.'
    comment = row[3].strip()
    return applicants, comment


def parse_xls(path_to_base, full_endpoint, number_to_continue):
    ''' Обрабатываем построчно все найденные xls файлы в указанной директории
    '''
    print('В указанной директории находятся следующие файлы')
    files = os.listdir(path_to_base)
    print(files)
    for file in files:
        if os.path.splitext(file)[1] == '.xlsx' or os.path.splitext(file)[1] == '.xls':
            wb = load_workbook(os.path.join(path_to_base, file))
            ws = wb.active
            # Проверяем , что найденный нами xls файл содержит нужную нам информацию.
            if ws['A1'].value == 'Должность' and ws['B1'].value == 'ФИО':
                print(f'Обрабатываем файл: {file}')
                data_xls = list(ws.values)
                for i in range(number_to_continue+1, len(data_xls)):
                    row = data_xls[i]
                    print(row)
                    applicants, comment = _get_data_from_row_xls(row)

                #  Пробуем получить id файлов при загрузке и в случае успеха, прикрепяем id к json конкретного кандидата
                    try:
                        files = upload_files(
                            fio=row[1].strip(),
                            position=applicants['position'].strip(),
                            path_to_base=path_to_base,
                            token=token,
                            full_endpoint=full_endpoint
                        )

                    except:
                        pass
                    if files:
                        applicants['externals'] = [{'files': files}]

                    # Сохраняем в базу данных кандидата
                    r = requests.post(
                        joinurl(full_endpoint, post_add_in_base), json=applicants, headers=headers)
                    logging.debug(applicants)
                    logging.debug(r.json())

                    if r.status_code == 200:
                        print(f'Кандидат {row[1]} добавлен в базу')
                    else:
                        print(
                            f'Ошибка при загрузке кандидата в базу. Строка {i+1}')
                        raise Exception(
                            f'Ошибка при загрузке кандидата в базу. Строка {i+1}')

                    # Получаем id  кандидата, чтобы использовать при записи на вакансию

                    id_applicants = r.json()['id']
                    #  Из словарей  получаем id  вакансии и статуса
                    id_vacancy = dict_id_vacancy.get(
                        row[0], 0)  # Получаем id Должности или 0
                    id_status = dict_id_status.get(
                        row[4], 0)  # Получаем id Статусв или 0

                    data = {
                        "vacancy": id_vacancy,
                        "status": id_status,
                        "comment": comment
                    }

                    # Собираем api для добавления кандидата на вакансию
                    post_for_vacancy = post_add_on_vacancy.split(
                        '{applicant_id}')
                    post_for_vacancy = joinurl(post_for_vacancy[0], str(
                        id_applicants))+post_for_vacancy[1]

                    # Сохраняем кандидата на вакансию
                    r = requests.post(
                        joinurl(full_endpoint, post_for_vacancy), json=data, headers=headers)

                    if r.status_code == 200:
                        print(f'Кандидат {row[1]} добавлен на вакансию')
                    else:
                        print(
                            f'Ошибка при добавлении кандидата на вакансию. Строка {i+1}')
                        raise Exception(
                            f'Ошибка при добавлении кандидата на вакансию. Строка {i+1}')
                    print('-------------------')


if __name__ == '__main__':

    try:
        params = pars_arg(sys.argv[1:])
        token = params.token
        path_to_base = params.path
        number_to_continue = params.number_to_continue

        headers = {'user-agent': 'App/1.0',
                   'Authorization': f'Bearer {token}',
                   }
        logging.debug(
            f'Получили параметры- token =  {token} path = {path_to_base}')

        # Получаем account_id  для запросов
        acc_id = get_account_id(
            joinurl(endpoint, accounts_id), headers=headers)
        if acc_id == -1:
            raise SystemExit(0)

        full_endpoint = joinurl(endpoint, 'account', acc_id)

        # Получаем  словарь и его id
        dict_id_vacancy = get_vacancies_id(full_endpoint, headers)
        # Получаем статус и его id
        dict_id_status = get_status_id(full_endpoint, headers)

        # Обработка xls
        parse_xls(
            '/home/max/Projects/testtask/huntflow/Тестовое задание/', full_endpoint, number_to_continue)

    except Exception as e:
        logging.exception(e)

from telebot import TeleBot, apihelper, types
from user_filter import UserFilter, kinds, sorts
import datetime
import time
from parser_class import AutoRUParser, AutoRuHelper

DATA_DIR = './data'
TOKEN_FILE = f'{DATA_DIR}/token.tlg'
FILTER_LIST = f'{DATA_DIR}/filters.list'
CARS_LIST = f'{DATA_DIR}/cars.list'
TOKEN = ''
ID_ADMIN = ''
filters = UserFilter(FILTER_LIST)
cars = AutoRuHelper(CARS_LIST)
parsers = {}
m_bot = None

try:
    with open(TOKEN_FILE, 'rt', encoding='utf-8') as f:
        TOKEN = f.readline().strip()
        ID_ADMIN = f.readline().strip()
except FileNotFoundError:
    print(f'Для работы необходим токен Tg, сохранённый первой строкой в файле "{TOKEN_FILE}".')
    exit(-1)
if len(ID_ADMIN) < 1:
    print(f'Для работы необходим идентификатор пользователя Tg, сохранённый второй строкой в файле "{TOKEN_FILE}".')
    exit(-1)
try:
    m_bot = TeleBot(TOKEN)
except ConnectionError:
    print('Не удалось установить соединение с Tg без прокси, попробуем через финнов...')
    m_proxy = {
        'http': 'http://95.217.95.130:58080',
        'https': 'http://95.217.95.130:58080'
    }
    apihelper.proxy = m_proxy
    try:
        m_bot = TeleBot(TOKEN)
    except ConnectionError:
        m_bot = None

if m_bot is None:
    print('''
С заданным proxy соединение всё равно не устанавливается.
Попробуйте задать в переменной m_proxy другой адрес, и перезапустить скрипт.
''')
else:
    m_markup_kinds = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    m_kind_buttons = []
    for key in kinds.keys():
        m_kind_buttons.append(types.KeyboardButton(kinds[key]))
        m_markup_kinds.row(m_kind_buttons[len(m_kind_buttons) - 1])

    m_markup_sorts = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    m_sort_buttons = {}
    for key in sorts.keys():
        m_sort_buttons[key] = types.KeyboardButton(sorts[key])
    m_markup_sorts.row(m_sort_buttons['fresh_relevance'], m_sort_buttons['cr_date-desc'])
    m_markup_sorts.row(m_sort_buttons['year-desc'], m_sort_buttons['year-asc'])
    m_markup_sorts.row(m_sort_buttons['price-desc'], m_sort_buttons['price-asc'])
    m_markup_sorts.row(m_sort_buttons['km_age-asc'])

    m_markup_cars = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    m_car_buttons = [types.KeyboardButton('Любой марки')]
    for i in range(0, len(cars)):
        m_car_buttons.append(types.KeyboardButton(cars[i]['name']))
    m_len = len(cars)
    m_limit = m_len // 5
    m_markup_cars.row(m_car_buttons[0])
    for i in range(1, m_limit * 5 + 1, 5):
        m_markup_cars.row(
            m_car_buttons[i],
            m_car_buttons[i+1],
            m_car_buttons[i+2],
            m_car_buttons[i+3],
            m_car_buttons[i+4]
        )
    m_rest = m_len - m_limit * 5
    if 1 == m_rest:
        m_markup_cars.row(m_car_buttons[m_limit * 5 + 1])
    elif 2 == m_rest:
        m_markup_cars.row(
            m_car_buttons[m_limit * 5 + 1],
            m_car_buttons[m_limit * 5 + 2]
        )
    elif 3 == m_rest:
        m_markup_cars.row(
            m_car_buttons[m_limit * 5 + 1],
            m_car_buttons[m_limit * 5 + 2],
            m_car_buttons[m_limit * 5 + 3]
        )
    elif 4 == m_rest:
        m_markup_cars.row(
            m_car_buttons[m_limit * 5 + 1],
            m_car_buttons[m_limit * 5 + 2],
            m_car_buttons[m_limit * 5 + 3],
            m_car_buttons[m_limit * 5 + 4]
        )

    print('Бот запущен и ждёт гостей.')

    @m_bot.message_handler(commands=['start', 'help'])
    def handle_help_cmd(msg):
        m_txt = f'''
Вас приветствует бот поиска автомобилей на AUTO.RU

Вот что я умею:
/start - начать работу с ботом
/name - задать марку автомобиля для поиска
/model - задать модель для поиска
/year - задать фильтр по годам выпуска авто, границы бот запрашивает автоматически
/price - задать фильтр по ценам, границы бот запрашивает автоматически
/kind - задать тип автомобилей: новые/с пробегом/все
/sort - задать режим сортировки
/filter - показать установленные условия поиска
/show - показать очередную страницу с результатами поиска
/show <page_no> - показать страницу номер <page_no> с результатами поиска
/clear - очистить параметры поиска
/help - выводит это окно
        '''
        if str(msg.from_user.id) == ID_ADMIN:
            m_txt += f'''
    
Команды, доступные только администратору:
/update - обновить список автомобилей и их моделей, по которым доступны объявления на сайте
/stat_auto - показать статистику по загруженной информации об автомобилях
/stat_user - показать сколько пользователей пользовались ботом
    '''
        if '/start' == msg.text:
            m_txt = f'Здравствуйте, *{msg.from_user.first_name}*!\n\n' + m_txt
            filters.register(msg.from_user.id)
        m_bot.send_message(msg.chat.id, m_txt)

    @m_bot.message_handler(commands=['update'])
    def handle_upd_auto_cmd(msg):
        if str(msg.from_user.id) == ID_ADMIN:
            m_bot.send_message(msg.chat.id, 'Получаем список популярных автомобилей...')
            cars.load()
            m_bot.send_message(msg.chat.id, 'Переходим к загрузке моделей этих авто...')
            for idx in range(0, len(cars)):
                cars.get_models(idx)
                m_bot.send_message(
                    msg.chat.id,
                    f'Для {cars[idx]["name"]} загружено моделей: {len(cars[idx]["models"])}'
                )
                time.sleep(2)
            cars.dump_data()
            m_bot.send_message(msg.chat.id, 'Загрузка данных завершена.')
        else:
            m_bot.send_message(msg.chat.id, 'Доступ запрещён.')

    @m_bot.message_handler(commands=['stat_auto'])
    def handle_stat_auto_cmd(msg):
        if str(msg.from_user.id) == ID_ADMIN:
            cnt_c = len(cars)
            cnt_m = 0
            for idx in range(0, len(cars)):
                if 'models' in cars[idx].keys():
                    cnt_m += len(cars[idx]['models'])
            m_bot.send_message(msg.chat.id, f'Загружено автомобилей: {cnt_c}\n  всего моделей: {cnt_m}')
        else:
            m_bot.send_message(msg.chat.id, 'Доступ запрещён.')


    @m_bot.message_handler(commands=['stat_user'])
    def handle_stat_user_cmd(msg):
        if str(msg.from_user.id) == ID_ADMIN:
            m_bot.send_message(msg.chat.id, f'Зарегистрировано пользователей: {len(filters)}')
        else:
            m_bot.send_message(msg.chat.id, 'Доступ запрещён.')

    @m_bot.message_handler(commands=['name'])
    def handle_name_cmd(msg):
        if msg.from_user.id in parsers:
            del parsers[msg.from_user.id]
        m_bot.send_message(msg.chat.id, 'Выберите марку автомобили :', reply_markup=m_markup_cars)
        m_bot.register_next_step_handler(msg, process_name_cmd)

    def process_name_cmd(msg):
        m_txt = msg.text
        m_chat = msg.chat.id
        has_data = False
        for idx in range(0, len(cars)):
            if m_txt == cars[idx]['name']:
                has_data = True
                filters.add_filter(msg.from_user.id, 'auto', cars[idx]['code'])
                m_bot.send_message(m_chat, 'Фильтр обновлён.')
        if 'Любой марки' == m_txt:
            has_data = True
            filters.add_filter(msg.from_user.id, 'auto', None)
            m_bot.send_message(m_chat, 'Фильтр обновлён.')
        if not has_data:
            m_bot.send_message(m_chat, 'Недопустимый ввод.')
            m_bot.send_message(m_chat, 'Выберите марку автомобили :', reply_markup=m_markup_cars)
            m_bot.register_next_step_handler(msg, process_name_cmd)

    def build_models_markup(mdl_dict):
        m_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        m_buttons = [types.KeyboardButton('Любой модели')]
        for k in mdl_dict.keys():
            m_buttons.append(types.KeyboardButton(mdl_dict[k]))
        m_len = len(mdl_dict)
        m_limit = m_len // 4
        m_markup.row(m_buttons[0])
        for i in range(1, m_limit * 4 + 1, 4):
            m_markup.row(
                m_buttons[i],
                m_buttons[i + 1],
                m_buttons[i + 2],
                m_buttons[i + 3]
            )
        m_rest = m_len - m_limit * 5
        if 1 == m_rest:
            m_markup.row(m_buttons[m_limit * 4 + 1])
        elif 2 == m_rest:
            m_markup.row(
                m_buttons[m_limit * 4 + 1],
                m_buttons[m_limit * 4 + 2]
            )
        elif 3 == m_rest:
            m_markup.row(
                m_buttons[m_limit * 4 + 1],
                m_buttons[m_limit * 4 + 2],
                m_buttons[m_limit * 4 + 3]
            )
        return m_markup

    @m_bot.message_handler(commands=['model'])
    def handle_model_cmd(msg):
        m_filter = filters[msg.from_user.id]
        if m_filter is None or 'auto' not in m_filter.keys() or m_filter['auto'] is None:
            m_bot.send_message(msg.chat.id, 'Сначала необходимо указать марку автомобиля.')
        else:
            m_car = None
            for i in range(0, len(cars)):
                if cars[i]['code'] == m_filter['auto']:
                    m_car = i
                    break
            if m_car is not None:
                if msg.from_user.id in parsers:
                    del parsers[msg.from_user.id]
                m_markup = build_models_markup(cars[m_car]['models'])
                m_bot.send_message(msg.chat.id, 'Выберите модель автомобиля:', reply_markup=m_markup)
                m_bot.register_next_step_handler(msg, process_model_cmd)
            else:
                m_bot.send_message(msg.chat.id, f'Ошибка: неизвестная модеарка автомобиля \"{m_filter["auto"]}\"')

    def process_model_cmd(msg):
        m_txt = msg.text
        m_chat = msg.chat.id
        m_filter = filters[msg.from_user.id]
        m_car = None
        for i in range(0, len(cars)):
            if cars[i]['code'] == m_filter['auto']:
                m_car = i
                break
        if m_car is not None:
            has_data = False
            for k in cars[m_car]['models'].keys():
                if m_txt == cars[m_car]['models'][k]:
                    has_data = True
                    filters.add_filter(msg.from_user.id, 'model', k)
                    m_bot.send_message(m_chat, 'Фильтр обновлён.')
            if 'Любой марки' == m_txt:
                has_data = True
                filters.add_filter(msg.from_user.id, 'model', None)
                m_bot.send_message(m_chat, 'Фильтр обновлён.')
            if not has_data:
                m_bot.send_message(m_chat, 'Недопустимый ввод.')
                m_markup = build_models_markup(cars[m_car]['models'])
                m_bot.send_message(m_chat, 'Выберите модель автомобиля:', reply_markup=m_markup)
                m_bot.register_next_step_handler(msg, process_model_cmd)
        else:
            m_bot.send_message(m_chat, 'Ошибка обработки. Требуется задать марку автомобиля.')

    @m_bot.message_handler(commands=['kind'])
    def handle_kind_cmd(msg):
        if msg.from_user.id in parsers:
            del parsers[msg.from_user.id]
        m_bot.send_message(
            msg.chat.id,
            'Выберите, какие автомобили Вы хотите видеть в результатах:',
            reply_markup=m_markup_kinds
        )
        m_bot.register_next_step_handler(msg, process_kind_cmd)

    def process_kind_cmd(msg):
        m_txt = msg.text
        m_chat = msg.chat.id
        if m_txt in ('все', 'новые', 'с пробегом'):
            for item in kinds.keys():
                if m_txt == kinds[item]:
                    filters.add_filter(msg.from_user.id, 'kind', item)
                    m_bot.send_message(m_chat, 'Фильтр обновлён.')
        else:
            m_bot.send_message(m_chat, 'Недопустимый ввод')
            m_bot.send_message(
                msg.chat.id,
                'Выберите, какие автомобили Вы хотите видеть в результатах:',
                reply_markup=m_markup_kinds
            )
            m_bot.register_next_step_handler(msg, process_kind_cmd)

    @m_bot.message_handler(commands=['year'])
    def handle_year_cmd(msg):
        if msg.from_user.id in parsers:
            del parsers[msg.from_user.id]
        m_chat = msg.chat.id
        m_bot.send_message(m_chat, 'Укажите нижнюю границу для фильтрации по году выпуска, или "нет"/"no",'
                                   'если она не важна:')
        m_bot.register_next_step_handler(msg, process_year_low)

    def process_year_low(msg):
        m_chat = msg.chat.id
        m_txt = msg.text
        if m_txt in ('no', 'нет'):
            filters.add_filter(msg.from_user.id, 'year_from', None)
            m_bot.send_message(m_chat, 'Теперь задайте верхнюю границу для фильтрации по году выпуска,'
                                       ' или "нет"/"no", если она не важна:')
            m_bot.register_next_step_handler(msg, process_year_high)
        else:
            if m_txt.isdigit():
                m_year = int(m_txt)
                if m_year < 1890:
                    m_bot.send_message(m_chat, 'Укажите год, больший 1890:')
                    m_bot.register_next_step_handler(msg, process_year_low)
                else:
                    filters.add_filter(msg.from_user.id, 'year_from', m_txt)
                    m_bot.send_message(m_chat, 'Теперь задайте верхнюю границу для фильтрации по году выпуска,'
                                               ' или "нет"/"no", если она не важна:')
                    m_bot.register_next_step_handler(msg, process_year_high)
            else:
                m_bot.send_message(m_chat, 'Неверный ввод, попробуйте ещё раз указать год:')
                m_bot.register_next_step_handler(msg, process_year_low)

    def process_year_high(msg):
        m_chat = msg.chat.id
        m_txt = msg.text
        if m_txt in ('no', 'нет'):
            filters.add_filter(msg.from_user.id, 'year_to', None)
            m_bot.send_message(m_chat, 'Фильтр успешно обновлён')
        else:
            if m_txt.isdigit():
                m_year = int(m_txt)
                if m_year > datetime.datetime.now().year:
                    m_bot.send_message(m_chat, 'Укажите год не из будущего:')
                    m_bot.register_next_step_handler(msg, process_year_high)
                else:
                    filters.add_filter(msg.from_user.id, 'year_to', m_txt)
                    m_bot.send_message(m_chat, 'Фильтр успешно обновлён')
            else:
                m_bot.send_message(m_chat, 'Неверный ввод, попробуйте ещё раз указать год:')
                m_bot.register_next_step_handler(msg, process_year_high)

    @m_bot.message_handler(commands=['price'])
    def handle_price_cmd(msg):
        if msg.from_user.id in parsers:
            del parsers[msg.from_user.id]
        m_chat = msg.chat.id
        m_bot.send_message(m_chat, 'Укажите нижнюю границу цены, или "нет"/"no", если она не важна:')
        m_bot.register_next_step_handler(msg, process_price_low)

    def process_price_low(msg):
        m_chat = msg.chat.id
        m_txt = msg.text
        if m_txt in ('no', 'нет'):
            filters.add_filter(msg.from_user.id, 'price_from', None)
            m_bot.send_message(m_chat, 'Теперь задайте верхнюю границу цены, или "нет"/"no", если она не важна:')
            m_bot.register_next_step_handler(msg, process_price_high)
        else:
            if m_txt.isdigit():
                m_value = int(m_txt)
                if m_value < 1000:
                    m_bot.send_message(m_chat, 'Укажите цену, не менее 1000 рублей:')
                    m_bot.register_next_step_handler(msg, process_price_low)
                else:
                    filters.add_filter(msg.from_user.id, 'price_from', m_txt)
                    m_bot.send_message(m_chat, 'Задайте верхнюю границу цены, или "нет"/"no", если она не важна:')
                    m_bot.register_next_step_handler(msg, process_price_high)
            else:
                m_bot.send_message(m_chat, 'Неверный ввод, попробуйте ещё раз указать цену:')
                m_bot.register_next_step_handler(msg, process_price_low)

    def process_price_high(msg):
        m_chat = msg.chat.id
        m_txt = msg.text
        if m_txt in ('no', 'нет'):
            filters.add_filter(msg.from_user.id, 'price_to', None)
            m_bot.send_message(m_chat, 'Фильтр успешно обновлён')
        else:
            if m_txt.isdigit():
                m_value = int(m_txt)
                if m_value < 1000:
                    m_bot.send_message(m_chat, 'Укажите цену, не менее 1000 рублей: ')
                    m_bot.register_next_step_handler(msg, process_price_high)
                else:
                    filters.add_filter(msg.from_user.id, 'price_to', m_txt)
                    m_bot.send_message(m_chat, 'Фильтр успешно обновлён')
            else:
                m_bot.send_message(m_chat, 'Неверный ввод, попробуйте ещё раз указать цену:')
                m_bot.register_next_step_handler(msg, process_price_high)

    @m_bot.message_handler(commands=['sort'])
    def handle_sorting_cmd(msg):
        if msg.from_user.id in parsers:
            del parsers[msg.from_user.id]
        m_bot.send_message(
            msg.chat.id,
            'Выберите тип сортировки:',
            reply_markup=m_markup_sorts
        )
        m_bot.register_next_step_handler(msg, process_sort_cmd)

    def process_sort_cmd(msg):
        m_sort = msg.text
        if m_sort not in sorts.values():
            m_bot.send_message(msg.chat.id, 'Неверный ввод.')
            m_bot.send_message(
                msg.chat.id,
                'Выберите тип сортировки:',
                reply_markup=m_markup_sorts
            )
            m_bot.register_next_step_handler(msg, process_sort_cmd)
        else:
            for s_key in sorts.keys():
                if m_sort == sorts[s_key]:
                    filters.add_filter(msg.from_user.id, 'sort', s_key)
                    m_bot.send_message(msg.chat.id, 'Фильтр обновлён.')
                    break

    @m_bot.message_handler(commands=['filter'])
    def handle_filter_cmd(msg):
        m_txt = filters.show(msg.from_user.id) or 'Ваш фильтр пуст.'
        if str(msg.from_user.id) == ID_ADMIN:
            m_txt += f'\n\n{filters.get_filter(msg.from_user.id)}'
        m_bot.send_message(msg.chat.id, m_txt)

    @m_bot.message_handler(commands=['show'])
    def handle_show_cmd(msg):
        m_data = msg.text.split(' ')
        m_idx = msg.from_user.id
        m_page = 0
        if len(m_data) == 2:
            if m_data[1].isdigit():
                m_page = int(m_data[1])
        if m_idx not in parsers.keys():
            parsers[m_idx] = AutoRUParser(filters.get_filter(m_idx))
        m_parser = parsers[m_idx]
        m_bot.send_message(msg.chat.id, 'Идёт подготовка данных, немного терпения...')
        m_parser.prepare_page(m_page)
        has_data = False
        for item in m_parser:
            m_bot.send_message(msg.chat.id, m_parser.beautify(item), disable_web_page_preview=True)
            time.sleep(1)
            has_data = True
        if not has_data:
            m_bot.send_message(msg.chat.id, 'Данных не найдено.')
        else:
            m_bot.send_message(msg.chat.id, f'Показан блок {m_parser.cur_page()} из {len(m_parser)}')

    @m_bot.message_handler(commands=['clear'])
    def handle_clear_cmd(msg):
        if msg.from_user.id in parsers:
            del parsers[msg.from_user.id]
        filters.clear(msg.from_user.id)
        m_bot.send_message(msg.chat.id, 'Фильтр поиска очищен.')

    @m_bot.message_handler(commands=['log_me'])
    def simple_react(msg):
        print(msg)
        m_bot.send_message(msg.chat.id, 'msg logged')

    m_bot.polling()

import requests
from bs4 import BeautifulSoup
import pickle
import os


URL = 'https://auto.ru'
PAGE_CONTROL = 'ControlGroup ControlGroup_responsive_no ControlGroup_size_s ListingPagination-module__pages'
PAGE_BUTTON = 'Button Button_color_whiteHoverBlue Button_size_s Button_type_link Button_width_default ListingPagination-module__page'

OBJ_CONTROL = 'ListingItem-module__description'
OBJ_TITLE = 'ListingItemTitle-module__container ListingItem-module__title'
OBJ_LINK = 'Link ListingItemTitle-module__link'
OBJ_DATA_ELEM = 'div'
OBJ_DATA = 'ListingItemTechSummary-module__cell'
OBJ_KM = 'ListingItem-module__kmAge'
OBJ_PRICE = 'ListingItemPrice-module__content'

NEW_CONTROL = 'ListingItemNewGroup__column ListingItemNewGroup__column_left'
NEW_TITLE = 'ListingItemTitle-module__container ListingItemNewGroup__title'
NEW_LINK = 'Link ListingItemTitle-module__link'
NEW_DATA_ELEM = 'dt'
NEW_DATA = 'ListingItemNewGroup__techSummaryValue'
NEW_PRICE = 'ListingItemNewGroup__price'


class AutoRUParser:

    def __init__(self, search='/cars/hyundai/ix35/2015-year/all/?sort=price-asc&output_type=list'):
        self._page = 0
        self._max_page = -1
        self._items = []
        self._url = f'{URL}{search}'
        self._cur = -1
        self._mode = 1  # 0 - поиск только новых авто, 1 - все другие режимы поиска

    def reset(self):
        if len(self._items) > 0:
            del self._items
        self._items = []
        self._cur = -1

    def prepare_page(self, page=0):
        need_request = True
        if 0 == page:
            self._page += 1
        elif page == self._page:
            need_request = False
        else:
            self._page = page
        if 0 < self._max_page < self._page:
            self.reset()
            need_request = False
        if need_request:
            self.reset()
            self._mode = 1 if self._url.find('/new/') < 0 else 0
            m_data = requests.get(f'{self._url}&page={self._page}')
            if 200 == m_data.status_code:
                m_soup = BeautifulSoup(m_data.text, 'html.parser')
                if -1 == self._max_page:
                    m_pages = m_soup.find('span', class_=PAGE_CONTROL)
                    if m_pages is not None:
                        m_page = m_pages.find_all('a', class_=PAGE_BUTTON)[-1]
                        self._max_page = int(m_page.text)
                    else:
                        self._max_page = 1
                for item in m_soup.find_all('div', class_=OBJ_CONTROL if self._mode else NEW_CONTROL):
                    self.load(item.encode('iso-8859-1').decode('utf-8'))
        pass

    def load(self, p_txt):
        m_result = {}
        m_soup = BeautifulSoup(p_txt, 'html.parser')
        # 1. Title, link
        m_obj = m_soup.find('h3', class_=OBJ_TITLE if self._mode else NEW_TITLE)
        if m_obj is not None:
            m_name = m_obj.find('a', class_=OBJ_LINK if self._mode else NEW_LINK)
            m_result['link'] = m_obj.a['href']
            if m_name is not None:
                m_result['name'] = m_name.text.strip()
        # 2. Value, Power, Fuel
        m_txt = m_soup.find_all(
            OBJ_DATA_ELEM if self._mode else NEW_DATA_ELEM
            , class_=OBJ_DATA if self._mode else NEW_DATA
            , limit=1
        )
        if len(m_txt) > 0:
            m_result['engine'] = m_txt[0].text.strip()
        else:
            m_result['engine'] = 'нет данных'
        # 3. KM
        if self._mode:
            m_obj = m_soup.find('div', class_=OBJ_KM)
            if m_obj is not None:
                m_result['km'] = m_obj.text.strip()
            else:
                m_result['km'] = 'нет данных'
        else:
            m_result['km'] = 'новый'
        # 4. Cost
        m_obj = m_soup.find('div', class_=OBJ_PRICE if self._mode else NEW_PRICE)
        if m_obj is not None:
            m_result['price'] = m_obj.text.strip()
        self._items.append(m_result)

    def __str__(self):
        m_str = ''
        for item in self._items:
            m_str += f'{self.beautify(item)}\n{"-"*80}\n'
        if len(m_str) < 1:
            m_str = f'Нет данных.\n{"-"*80}\n'
        m_str += f'Страница {self._page} из {self._max_page}\n\n'
        return m_str

    @staticmethod
    def beautify(item):
        m_str = f'{item["name"]}\n   цена: {item["price"]}\n'
        m_str += f'   двигатель: {item["engine"]}\n'
        m_str += f'   пробег: {item["km"]}\n'
        m_str += f'Объявление: {item["link"]}'
        return m_str

    def cur_page(self):
        return self._page

    def __len__(self):
        return self._max_page

    def __next__(self):
        if self._cur + 1 >= len(self._items):
            raise StopIteration()
        else:
            self._cur += 1
        return self._items[self._cur]

    def __iter__(self):
        return self

    def __getitem__(self, item):
        if 0 <= item < len(self._items):
            return self._items[item]


class AutoRuHelper:

    def __init__(self, path):
        self._path = path
        self._item = -1
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self._cars = pickle.load(f)
        else:
            self._cars = []

    def __iter__(self):
        return self

    def __next__(self):
        if self._item + 1 >= len(self._cars):
            raise StopIteration()
        else:
            self._item += 1
        return self._cars[self._item]

    def __getitem__(self, item):
        if 0 <= item < len(self._cars):
            return self._cars[item]

    def __len__(self):
        return len(self._cars)

    def dump_data(self):
        with open(self._path, 'wb') as f:
            pickle.dump(self._cars, f)

    def load(self):
        if len(self._cars) > 0:
            self._cars.clear()
        m_data = requests.get(f'{URL}')
        if 200 == m_data.status_code:
            m_soup = BeautifulSoup(m_data.text.encode('iso-8859-1').decode('utf-8'), 'html.parser')
            m_obj = m_soup.find('div', 'IndexMarks')
            if m_obj is not None:
                m_cols = m_obj.find_all('div', 'IndexMarks__col')
                for col in m_cols:
                    m_list = col.find_all('a', 'IndexMarks__item')
                    for item in m_list:
                        m_link = item.get('href')
                        m_code = m_link.split('/')[-3]
                        m_txt = item.div.text.strip()
                        self._cars.append({'name': m_txt, 'link': m_link, 'code': m_code})

    def get_models(self, p_idx):
        m_item = self._cars[p_idx]
        m_item['models'] = {}
        if m_item is not None:
            m_data = requests.get(f'{m_item["link"]}')
            if 200 == m_data.status_code:
                m_soup = BeautifulSoup(m_data.text.encode('iso-8859-1').decode('utf-8'), 'html.parser')
                # 'ListingPopularMMM-module__container PageListing-module__popularMMM'
                m_obj = m_soup.find('div', id='popularMMM')
                if m_obj is not None:
                    m_cols = m_obj.find_all('div', 'ListingPopularMMM-module__column')
                    for col in m_cols:
                        m_list = col.find_all('a', 'Link ListingPopularMMM-module__itemName')
                        for item in m_list:
                            m_code = item.get('href').split('/')[-3]
                            m_name = item.text
                            m_item['models'][m_code] = m_name


if '__main__' == __name__:
    # m_info = AutoRUParser('/cars/new/?sort=price-desc&year_from=2015&year_to=2018&price_from=15000&price_to=600000&output_type=list')
    # m_info.prepare_page()
    # for i in m_info:
    #     print(m_info.beautify(i))
    # print('+'*15)
    # print(m_info)
    # while m_info.cur_page() <= len(m_info):
    #     print(m_info)
    #     time.sleep(10)
    #     m_info.prepare_page()
    m_cars = AutoRuHelper('./data/cars.list')
    z = 0
    # m_cars.load()
    for i in range(0, len(m_cars)):
        z += len(m_cars[i]["models"])
        print(f'{i}...{m_cars[i]["name"]:<20} - {len(m_cars[i]["models"])}')
    print(z)
    # m_cars.get_models(0)
    for k in m_cars[0]['models'].keys():
        print(k, '-->', m_cars[0]['models'][k])
    # m_cars.get_models(0)
    # print(m_cars[0])

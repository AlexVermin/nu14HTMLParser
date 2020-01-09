import requests
from bs4 import BeautifulSoup
import time


URL = 'https://auto.ru/cars/hyundai/ix35/2015-year/all/?sort=price-asc&output_type=list'


class AutoRU:

    def __init__(self):
        self._name = ''
        self._power = ''
        self._cost = ''
        self._value = ''
        self._km = ''
        self._fuel = ''
        self._link = ''

    def reset(self):
        self._name = ''
        self._power = ''
        self._cost = ''
        self._value = ''
        self._km = ''
        self._fuel = ''
        self._link = ''

    def load(self, p_txt):
        m_soup = BeautifulSoup(p_txt, 'html.parser')
        # 1. Title, link
        m_obj = m_soup.find('h3', class_='ListingItemTitle-module__container ListingItem-module__title')
        if m_obj is not None:
            m_name = m_obj.find('a', class_='Link ListingItemTitle-module__link')
            self._link = m_obj.a['href']
            if m_name is not None:
                self._name = m_name.text.strip()
        # 2. Value, Power, Fuel
        m_obj = m_soup.find('div', class_='ListingItem-module__description')
        if m_obj is not None:
            m_txt = m_obj.find('div', class_='ListingItemTechSummary-module__cell')
            # m_txt = m_txt.replace(('\xa', '\u2009'), ('', ''))
            m_values = m_txt.text.split('/')
            self._value = m_values[0].strip()
            self._power = m_values[1].strip()
            self._fuel = m_values[2].strip()
        # 3. KM
        m_obj = m_soup.find('div', class_='ListingItem-module__kmAge')
        if m_obj is not None:
            self._km = m_obj.text.strip()
        # 4. Cost
        m_obj = m_soup.find('div', class_='ListingItemPrice-module__content')
        if m_obj is not None:
            self._cost = m_obj.text.strip()

    def __str__(self):
        m_str = f'Марка: {self._name}, цена: {self._cost}, объём двигателя: {self._value}\n'
        m_str += f'     мощность двигателя: {self._power}, тип топлива: {self._fuel}\n     пробег: {self._km}\n'
        m_str += f'     ссылка на объявление: {self._link}'
        return m_str


if '__main__' == __name__:
    cnt = 1
    page = 1
    max_page = 1
    m_info = AutoRU()
    m_data = requests.get(URL)
    if 200 == m_data.status_code:
        m_soup = BeautifulSoup(m_data.text, 'html.parser')
        m_pages = m_soup.find('span', class_='ControlGroup ControlGroup_responsive_no ControlGroup_size_s ListingPagination-module__pages')
        if m_pages is not None:
            m_page = m_pages.find_all('a', class_='Button Button_color_whiteHoverBlue Button_size_s Button_type_link Button_width_default ListingPagination-module__page')[-1]
            max_page = int(m_page.text)
        while True:
            for item in m_soup.find_all('div', class_='ListingItem-module__description'):
                m_info.reset()
                m_info.load(item.encode('iso-8859-1').decode('utf-8'))
                print(f'{cnt:<6} --- Страница {page} из {max_page} {"-"*80}\n{m_info}')
                cnt += 1
            page += 1
            if page <= max_page:
                time.sleep(10)
                m_data = requests.get(f'{URL}&page={page}')
                if 200 == m_data.status_code:
                    m_soup = BeautifulSoup(m_data.text, 'html.parser')
                else:
                    print(f'Не удалось получить данные о {page}-й странице с сайта.')
                    break
            else:
                break
    else:
        print('Не удалось получить данные с сайта.')

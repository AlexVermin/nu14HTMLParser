import pickle
import os

kinds = dict(all='все', new='новые', used='с пробегом')

sorts = {
    'fresh_relevance': 'актуальные',
    'cr_date-desc': 'по дате создания, сначала новые',
    'year-desc': 'по году выпуска, сначала новые',
    'year-asc': 'по году выпуска, сначала старые',
    'km_age-asc': 'по пробегу',
    'price-asc': 'по цене, сначала дешёвые',
    'price-desc': 'по цене, сначала дорогие'
}


class UserFilter:

    def __init__(self, path):
        self._path = path
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self._items = pickle.load(f)
        else:
            self._items = {}

    def dump(self):
        with open(self._path, 'wb') as f:
            pickle.dump(self._items, f)

    def __len__(self):
        return len(self._items)

    def show(self, idx):
        m_txt = ''
        if idx not in self._items.keys():
            self._items[idx] = {}
            self.dump()
        if 'auto' in self._items[idx].keys() and self._items[idx]["auto"] is not None:
            m_txt += f'Марка автомобиля: {self._items[idx]["auto"]}\n'
        else:
            m_txt += f'Марка автомобиля: любой\n'
        if 'model' in self._items[idx].keys():
            m_txt += f'Модель автомобиля: {self._items[idx]["model"]}\n'
        else:
            m_txt += f'Модель автомобиля: любая\n'
        if 'year_from' in self._items[idx].keys() or 'year_to' in self._items[idx].keys():
            m_txt += f'Год выпуска: '
            if 'year_from' in self._items[idx].keys() and self._items[idx]['year_from'] is not None:
                m_txt += f'от {self._items[idx]["year_from"]} '
            if 'year_to' in self._items[idx].keys() and self._items[idx]['year_to'] is not None:
                m_txt += f'до {self._items[idx]["year_to"]} '
            if (
                'year_from' in self._items[idx].keys() and self._items[idx]['year_from'] is None
                or 'year_to' in self._items[idx].keys() and self._items[idx]['year_to'] is None
            ):
                m_txt += 'не важен'
            m_txt += '\n'
        else:
            m_txt += f'Год выпуска: не важен\n'
        if 'price_from' in self._items[idx].keys() or 'price_to' in self._items[idx].keys():
            m_txt += f'Стоимость в рублях: '
            if 'price_from' in self._items[idx].keys() and self._items[idx]['price_from'] is not None:
                m_txt += f'от {self._items[idx]["price_from"]} '
            if 'price_to' in self._items[idx].keys() and self._items[idx]['price_to'] is not None:
                m_txt += f'до {self._items[idx]["price_to"]} '
            if (
                'price_from' in self._items[idx].keys() and self._items[idx]['price_from'] is None
                or 'price_to' in self._items[idx].keys() and self._items[idx]['price_to'] is None
            ):
                m_txt += 'любая'
            m_txt += '\n'
        else:
            m_txt += f'Стоимость в рублях: любая\n'
        if 'kind' in self._items[idx].keys():
            m_txt += f'Виды автомобилей: {kinds[self._items[idx]["kind"]]}\n'
        else:
            m_txt += f'Виды автомобилей: все\n'
        if 'sort' in self._items[idx].keys():
            m_txt += f'Режим сортировки: {sorts[self._items[idx]["sort"]]}'
        else:
            m_txt += f'Режим сортировки: по актуальности'
        if len(m_txt) > 0:
            m_txt = f'Текущие параметры фильтрации:\n\n{m_txt}'

        return m_txt

    def register(self, idx):
        if idx not in self._items.keys():
            self._items[idx] = {}
            self.dump()

    def clear(self, idx):
        if idx in self._items.keys():
            del self._items[idx]
        self._items[idx] = {}
        self.dump()

    def add_filter(self, idx, key, value):
        if idx in self._items.keys():
            self._items[idx][key] = value
        else:
            self._items[idx] = {key: value}
        self.dump()

    def get_filter(self, idx):
        m_url = '/cars'
        if idx not in self._items.keys():
            self._items[idx] = {}
        m_obj = self._items[idx]
        m_keys = m_obj.keys()
        if 'auto' in m_keys and m_obj['auto'] is not None:
            m_url += f'/{m_obj["auto"]}'
            if 'model' in m_keys and m_obj['model'] is not None:
                m_url += f'/{m_obj["model"]}'
        if 'kind' not in m_keys or m_obj['kind'] is None:
            m_url += '/all'
        else:
            m_url += f'/{m_obj["kind"]}'
        if 'sort' not in m_keys or m_obj['sort'] is None:
            m_url += '/?sort=fresh_relevance'
        else:
            m_url += f'/?sort={m_obj["sort"]}'
        if 'year_from' in m_keys and m_obj['year_from'] is not None:
            m_url += f'&year_from={m_obj["year_from"]}'
        if 'year_to' in m_keys and m_obj['year_to'] is not None:
            m_url += f'&year_to={m_obj["year_to"]}'
        if 'price_from' in m_keys and m_obj['price_from'] is not None:
            m_url += f'&price_from={m_obj["price_from"]}'
        if 'price_to' in m_keys and m_obj['price_to'] is not None:
            m_url += f'&price_to={m_obj["price_to"]}'
        return f'{m_url}&output_type=list'

    def __getitem__(self, item):
        if item in self._items.keys():
            return self._items[item]

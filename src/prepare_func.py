import numpy as np
import pandas as pd
from datetime import datetime
import re


def process_prices(df):
    # Гипотеза, что у продвигаемых объявлений нереалистичная цена - уменьшаем ее на 5%
    df['Цена'] = np.where(df['Продвижения'].notna(),
                          df['Цена'] * 0.95,
                          df['Цена'])
    # Логарифмируем цену чтобы сгладить выбросы
    df = df.assign(log_price=np.log1p(df['Цена']))
    df = df.drop(['Продвижения'], axis=1)
    # Убираем выбросы
    top_quantile = df['log_price'].quantile(0.975)
    low_quantile = df['log_price'].quantile(0.025)
    return df[(df['log_price'] > low_quantile) & (df['log_price'] < top_quantile)]


def remove_unused(df):
    # Оставляем только нужные колонки и оставляем только ижс
    df = df.drop(['Пр.Всего', 'Пр.Сегод.', 'Кол-во знак.', 'Цена', 'Цена м²', 'ОбщПлощ', 'Отделка', 'Ссылка',
                  'Фото шт.', 'Фото', 'Unnamed: 50', 'Unnamed: 51', 'Продавец', 'Этаж', 'Ссылка', 'Широта',  'Долгота',
                  'Unnamed: 52', 'Unnamed: 53', 'Unnamed: 54', 'Unnamed: 55', 'Метро1', 'Метро2', 'Метро3', 'Улица',
                  'Район', 'Поселок', 'Мкр-н', 'Гор.Округ',
                  'Unnamed: 56', 'Unnamed: 57', 'Unnamed: 58', 'Unnamed: 59',
                  'Unnamed: 60', 'Unnamed: 61', 'Unnamed: 62', 'Unnamed: 63',
                  'Unnamed: 64', 'Unnamed: 65', 'Unnamed: 66', 'Unnamed: 67',
                  'Unnamed: 68', 'Unnamed: 69', 'Unnamed: 70', 'Unnamed: 71',
                  'Unnamed: 72', 'Unnamed: 73', 'Unnamed: 74', 'Unnamed: 75',
                  'Unnamed: 76', 'Unnamed: 77', 'Unnamed: 78', 'Unnamed: 79',
                  'Unnamed: 80', 'Unnamed: 81', 'Unnamed: 82', 'Unnamed: 83',
                  'Unnamed: 84', 'Unnamed: 85', 'Unnamed: 86', 'Unnamed: 87', 'Unnamed: 48',
                  'Unnamed: 88', 'Unnamed: 89', 'Unnamed: 90', 'Время поднятия',
                  'Unnamed: 49', 'Unnamed: 91', 'Unnamed: 92', 'Позиция', 'Пониж.цена', '№ объяв.',
                  'Unnamed: 93'], axis=1, errors='ignore')
    categories_to_keep = ['Дома', 'Коттеджи', 'Таунхаусы']
    df = df[df['Подкатегория'].isin(categories_to_keep)]
    df = df.drop(['Подкатегория'], axis=1)
    category = ['индивидуальное жилищное строительство (ИЖС)']
    df = df[df['Категория земель'].isin(category)]
    return df.drop(['Категория земель'], axis=1)


def extract_number(value):
    if pd.isna(value):
        return np.nan
    match = re.search(r'\d+(?:\.\d+)?', str(value))
    if match:
        return float(match.group())
    return np.nan


def encode_as_float(df, columns):
    for col in columns:
        df[col] = df[col].apply(extract_number)
    df = df.dropna(subset=columns)
    return df


def encode_toilet(df):
    def _encode(value):
        if pd.isna(value):
            return np.nan
        elif 'на улице' in str(value).lower() and 'в доме' in str(value).lower():
            return 2
        elif 'в доме' in str(value).lower():
            return 1
        elif 'на улице' in str(value).lower():
            return 0
        else:
            return np.nan

    df['Санузел'] = df['Санузел'].apply(_encode)
    return df.dropna(subset=['Санузел'])


def encode_city_center_distance(df):
    def _encode(distance):
        if pd.isna(distance):
            return 'Нет данных'
        if distance < 17:
            return 'Близко к городу'
        else:
            return 'Далеко от города'

    df['Расстояние до центра города'] = df['Расстояние до центра города'].apply(
        extract_number).astype(float)
    df['Расстояние_до_центра_города'] = df['Расстояние до центра города'].apply(
        _encode)
    df = pd.get_dummies(
        df, columns=['Расстояние_до_центра_города'], prefix='Расст_центр', dtype=int)
    return df.drop('Расстояние до центра города', axis=1)


def encode_amenities(df):
    def _encode(row):
        description = str(row['Описание']).lower()
        for_leisure = str(row['Для отдыха']).lower(
        ) if pd.notna(row['Для отдыха']) else ''

        has_banya = (
            'баня' in description or 'баня' in for_leisure or 'сауна' in description or 'сауна' in for_leisure)
        has_pool = ('бассейн' in description or 'бассейн' in for_leisure)

        return pd.Series({'Есть_баня': has_banya, 'Есть_бассейн': has_pool})

    df[['Есть_баня', 'Есть_бассейн']] = df.apply(_encode, axis=1)
    return df.drop('Для отдыха', axis=1, errors='ignore')


def encode_infrastructure(df):
    def _encode(row):
        description = str(row['Описание']).lower()
        infrastructure = str(row['Инфраструктура']).lower(
        ) if pd.notna(row['Инфраструктура']) else ''

        has_shop = ('магазин' in description or 'магазин' in infrastructure)
        has_pharmacy = ('аптек' in description or 'аптека' in infrastructure)
        has_kindergarten = (
            'детский сад' in description or 'детский сад' in infrastructure)
        has_school = ('школ' in description or 'школа' in infrastructure)

        return pd.Series({'Есть_магазин': has_shop, 'Есть_аптека': has_pharmacy, 'Есть_детский_сад': has_kindergarten, 'Есть_школа': has_school})

    df[['Есть_магазин', 'Есть_аптека', 'Есть_детский_сад',
        'Есть_школа']] = df.apply(_encode, axis=1)
    return df.drop('Инфраструктура', axis=1, errors='ignore')


def encode_tv_wifi(df):
    def _encode(row):
        description = str(row['Описание']).lower()
        tv_wifi = str(row['Интернет/ТВ']
                      ).lower() if pd.notna(row['Интернет/ТВ']) else ''

        has_tv = ('телевидение' in description or 'телевидение' in tv_wifi)
        has_wifi = (
            'wi-fi' in description or 'wi-fi' in tv_wifi or 'интернет' in description or 'вайфай' in description)

        return pd.Series({'Есть_wifi': has_wifi, 'Есть_tv': has_tv})

    df[['Есть_wifi', 'Есть_tv']] = df.apply(_encode, axis=1)
    return df.drop('Интернет/ТВ', axis=1, errors='ignore')


def encode_rooms(df):
    def _encode(value):
        if value == 'Свободная планировка':
            return np.nan
        elif value == '10 и больше':
            return 10.0
        else:
            try:
                return float(value)
            except ValueError:
                return np.nan

    df['Кол-воКомн_encoded'] = df['Кол-воКомн'].apply(_encode)
    df['Свободная_планировка'] = (df['Кол-воКомн'] == 'Свободная планировка')
    median_rooms = df['Кол-воКомн_encoded'].median()
    df['Кол-воКомн_encoded'] = df['Кол-воКомн_encoded'].fillna(median_rooms)
    return df.drop('Кол-воКомн', axis=1)


def encode_repair(df):
    df = df.dropna(subset=['Ремонт'])
    repair_dummies = pd.get_dummies(df['Ремонт'], prefix='Ремонт', dtype=bool)
    df = pd.concat([df, repair_dummies], axis=1)
    return df.drop('Ремонт', axis=1)


def encode_wall_material(df):
    df = df[df['МатериалСтен'].notna()]
    wall_material_dummies = pd.get_dummies(
        df['МатериалСтен'], prefix='МатериалСтен')
    df = df.drop('МатериалСтен', axis=1)
    df = pd.concat([df, wall_material_dummies], axis=1)
    return df


def encode_parking(df):
    def _encode(row):
        description = str(row['Описание']).lower()
        parking = str(row['Парковка']).lower(
        ) if pd.notna(row['Парковка']) else ''

        has_parking = (
            'парковочное' in description or 'парковочное' in parking or 'парковк' in description)
        has_garage = ('гараж' in description or 'гараж' in parking)

        return pd.Series({'Есть_парковка': has_parking, 'Есть_гараж': has_garage})

    df[['Есть_парковка', 'Есть_гараж']] = df.apply(_encode, axis=1)
    return df.drop('Парковка', axis=1, errors='ignore')


def encode_mortgage(df):
    def _encode(row):
        mortgage = str(row['Способ продажи']).lower(
        ) if pd.notna(row['Способ продажи']) else ''
        mortgage_available = ('возможна ипотека' in mortgage)
        return pd.Series({'Возможна_ипотека': mortgage_available})

    df[['Возможна_ипотека']] = df.apply(_encode, axis=1)
    return df.drop('Способ продажи', axis=1, errors='ignore')


def encode_terrace(df):
    def _encode(row):
        description = str(row['Описание']).lower()
        terrace = str(row['Терраса или веранда']).lower(
        ) if pd.notna(row['Терраса или веранда']) else ''

        has_terrace = (
            'веранд' in description or 'есть' in terrace or 'террас' in description or 'балкон' in description)
        return pd.Series({'Есть_терраса': has_terrace})

    df[['Есть_терраса']] = df.apply(_encode, axis=1)
    return df.drop('Терраса или веранда', axis=1, errors='ignore')


def encode_transport(df):
    def _encode(row):
        description = str(row['Описание']).lower()
        transport = str(row['Транспортная доступность']).lower(
        ) if pd.notna(row['Транспортная доступность']) else ''

        asphalt = (
            'асфальтированная дорога' in transport or 'асфальт' in description)
        public_transport = ('остановка общественного транспорта' in transport or
                            'автобус' in description or
                            'маршрутка' in description or
                            'общественный транспорт' in description)
        railway = ('железнодорожная станция' in transport or
                   'жд' in description or
                   'железнодорожная' in description or
                   'электричка' in description)

        return pd.Series({
            'Есть_асфальт': asphalt,
            'Есть_общ_транспорт': public_transport,
            'Есть_жд': railway
        })

    df[['Есть_асфальт', 'Есть_общ_транспорт', 'Есть_жд']
       ] = df.apply(_encode, axis=1)
    return df.drop('Транспортная доступность', axis=1, errors='ignore')


def process_year(df):
    current_year = datetime.now().year

    def calculate_age(year):
        current_year = datetime.now().year
        if pd.isna(year) or year == 0:
            return np.nan
        try:
            year = int(float(year))
            if year > current_year or year < 1800:
                return np.nan
            age = current_year - year
            return max(0, age)
        except ValueError:
            return np.nan

    df['ВозрастДома'] = df['ГодПостр'].apply(calculate_age)
    median_age = df['ВозрастДома'].median()
    df['ВозрастДома'] = df['ВозрастДома'].fillna(median_age)

    if median_age == 0 or np.isnan(median_age):
        df['ВозрастДома'] = df['ВозрастДома'].fillna(df['ВозрастДома'].mean())
        df['ВозрастДома'] = df['ВозрастДома'].fillna(15)

    df.loc[df['ВозрастДома'] > current_year - 1800, 'ВозрастДома'] = np.nan
    df['ВозрастДома'] = df['ВозрастДома'].fillna(df['ВозрастДома'].median())

    def categorize_age(age):
        if age < 5:
            return 'New (0-5 years)'
        elif age < 10:
            return 'Recent (5-10 years)'
        elif age < 20:
            return 'Modern (10-20 years)'
        elif age < 40:
            return 'Established (20-40 years)'
        else:
            return 'Old (40+ years)'

    df['ВозрастКатегория'] = df['ВозрастДома'].apply(categorize_age)
    df = pd.get_dummies(
        df, columns=['ВозрастКатегория'], prefix='Возраст', dtype=int)

    return df.drop('ГодПостр', axis=1)


def encode_utilities(df):
    def _encode(row):
        description = str(row['Описание']).lower()
        utils = str(row['Коммуникации']).lower() if pd.notna(
            row['Коммуникации']) else ''

        has_elec = ('электрич' in description or 'электричество' in utils)
        has_heat = ('отопление' in description or 'отопление' in utils)
        has_gas = ('газ' in description or 'газ' in utils)
        has_sew = ('канализац' in description or 'канализация' in utils)

        return pd.Series({'Есть_электричество': has_elec, 'Есть_отопление': has_heat, 'Есть_газ': has_gas, 'Есть_канализация': has_sew})

    df[['Есть_электричество', 'Есть_газ', 'Есть_отопление',
        'Есть_канализация']] = df.apply(_encode, axis=1)
    return df.drop('Коммуникации', axis=1, errors='ignore')


def add_region(df):
    def get_region(row):
        if pd.notna(row['Область']):
            return row['Область']
        elif pd.notna(row['Край']):
            return row['Край']
        elif pd.notna(row['Адрес']):
            region = row['Адрес'].split(',')[0].strip()
            if "р-н" in region:
                return row['Город']
            return region
        else:
            return row['Город']

    df['Регион'] = df.apply(get_region, axis=1)

    # Count the occurrences of each region
    region_counts = df['Регион'].value_counts()

    regions_to_keep = region_counts[region_counts >= 10].index

    df = df.drop(['Область', 'Край', 'Адрес'], axis=1)
    df = df[df['Регион'].isin(regions_to_keep)]
    df = df[df['Регион'].isin(regions_to_keep)]
    return df.dropna(subset=['Регион'])


def normalize_region_name(name):
    # Обновленный словарь для замены сокращений и стандартизации названий
    replacements = {
        'обл.': 'область',
        'АО': 'автономный округ',
        'Респ.': 'Республика',
        'г.': 'город',
        'г.о.': 'городской округ',
        'автономный округ': 'АО',
        'город ': '',  # Убираем слово "город" перед названиями городов
        'в том числе ': '',  # Убираем фразу "в том числе"
        ' без авт. округа': '',  # Убираем фразу "без авт. округа"
        'Уфа': 'Республика Башкортостан',
        'Казань': 'Республика Татарстан',
        'Махачкала': 'Республика Дагестан',
        'Мамадышский тракт': 'Республика Татарстан',
        'Ижевск': 'Удмуртская Республика',
        'Улан-Удэ': 'Республика Бурятия',
        "Владикавказ": "Республика Северная Осетия - Алания",
        "Нальчик": "Кабардино-Балкарская Республика",
        "Чебоксары": "Чувашская Республика",
        "Набережные Челны": "Республика Татарстан",
        "Петрозаводск": "Республика Карелия",
        "Семендер": "Республика Дагестан",
        "Ленинкент": "Республика Дагестан",
        "Стерлитамак": "Республика Башкортостан",
        "Беслан": "Республика Северная Осетия - Алания",
        "Моздок": "Республика Северная Осетия - Алания",
        "Саранск": "Республика Мордовия",
        "Алагир": "Республика Северная Осетия - Алания",
        "Гизель": "Республика Северная Осетия - Алания",
        "Архонская": "Республика Северная Осетия - Алания",
        "Новый Хушет": "Республика Дагестан",
        "Ардон": "Республика Северная Осетия - Алания",
        "Красносельское шоссе": "г.Санкт-Петербург",
        "Московское шоссе": "г.Санкт-Петербург",
        "Горское шоссе": "Республика Северная Осетия - Алания",
        "Волхонское шоссе": "г.Санкт-Петербург",
        "Новосибирский район": "Новосибирская область",
    }

    # Замена сокращений
    for old, new in replacements.items():
        name = name.replace(old, new)

    # Удаление лишних пробелов
    name = re.sub(r'\s+', ' ', name).strip()

    # Особые случаи
    if "Санкт-Петербург" in name:
        return "г.Санкт-Петербург"
    if "Москва" in name:
        return "г.Москва"

    if "Осетия" in name:
        return "Республика Северная Осетия - Алания"

    return name


def add_district_and_salary(df):
    df_salary_data = pd.read_csv('./data/additional_data/salary_region.csv')

    # Нормализация названий регионов в обоих DataFrame
    df['Регион'] = df['Регион'].apply(normalize_region_name)
    df_salary_data['Регион'] = df_salary_data['Регион'].apply(
        normalize_region_name)

    # Создание словарей для маппинга
    okrug = dict(zip(df_salary_data['Регион'], df_salary_data['Округ']))
    salary = dict(zip(df_salary_data['Регион'], df_salary_data['ЗП']))

    # Маппинг данных
    df['Округ'] = df['Регион'].map(okrug)
    df['ЗП'] = df['Регион'].map(salary)

    df = df.dropna(subset=['ЗП'])
    return df


def add_population(df):
    def normalize_string(s):
        if pd.isna(s):
            return s
        s = s.lower()
        s = re.sub(r'[^a-zа-я0-9\s]', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    population_data = pd.read_csv('./data/additional_data/city_population.csv')
    population_data = population_data.rename(columns={
        "key": "Город",
        "population": "Население"
    })

    df["Город"] = df["Город"].apply(normalize_string) + ' ' + df["Регион"].apply(
        normalize_string) if 'Регион' in df.columns else df["Город"].apply(normalize_string) + ' ' + 'московская область'

    merged_df = df.merge(population_data[['Город', 'Население']],
                         on=["Город"],
                         how="left")

    merged_df['Население'] = merged_df['Население'].fillna(0)

    return merged_df


def remove_outliers(df, columns):
    """
    Remove outliers from specified columns using the IQR method.

    :param df: DataFrame
    :param columns: List of column names to remove outliers from
    :return: DataFrame with outliers removed
    """
    for column in columns:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    return df


def process_floors(df):
    df['Кол-воЭтаж'] = df['Кол-воЭтаж'].apply(extract_number)

    # Fill NaN values with the median
    median_floors = df['Кол-воЭтаж'].median()
    df['Кол-воЭтаж'] = df['Кол-воЭтаж'].fillna(median_floors)

    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    column_mapping = {
        'Площ.дома': 'Площ_дома',
        'Площ.Участка': 'Площ_Участка',
        'Кол-воЭтаж': 'Кол_воЭтаж',
        'Расст_центр_Близко к городу': 'Расст_центр_Близко_к_городу',
        'Расст_центр_Далеко от города': 'Расст_центр_Далеко_от_города',
        'Расст_центр_Нет данных': 'Расст_центр_Нет_данных',
        'Кол-воКомн_encoded': 'Кол_воКомн_encoded',
        'Ремонт_требует ремонта': 'Ремонт_требует_ремонта',
        'МатериалСтен_железобетонные панели': 'МатериалСтен_железобетонные_панели',
        'МатериалСтен_сэндвич-панели': 'МатериалСтен_сэндвич_панели',
        'МатериалСтен_экспериментальные материалы': 'МатериалСтен_экспериментальные_материалы',
        'Возраст_Established (20-40 years)': 'Возраст_Established_20_40_years',
        'Возраст_Modern (10-20 years)': 'Возраст_Modern_10_20_years',
        'Возраст_New (0-5 years)': 'Возраст_New_0_5_years',
        'Возраст_Old (40+ years)': 'Возраст_Old_40_plus_years',
        'Возраст_Recent (5-10 years)': 'Возраст_Recent_5_10_years',
        'Расстояние от МКАД': 'Расстояние_от_МКАД'
    }
    return df.rename(columns=column_mapping, errors='ignore')

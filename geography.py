"""
A variety of odds and ends to help clean user-submitted location data from
NUFORC's online database.
@author: MoonJam
"""

import requests
from pandas import Series, concat
from bs4 import BeautifulSoup


def clean_iso(df):
    """Simple if/else match to clean country names that might have ones not
    likely used by the generally American/Canadian submitters of NUFORC data.
    """

    iso_code = df['Code']

    code_list = ['BO', 'CC', 'FK', 'FM', 'IR', 'KP', 'MF', 'SX', 'VE', 'VG',
                 'VI', 'CD', 'KR', 'MD', 'PS', 'TW', 'TZ']

    name_list = ['Bolivia', 'Cocos Islands', 'Falkland Islands', 'Micronesia',
                 'Iran', 'North Korea', 'Saint Martin', 'Sint Maarten',
                 'Venezuela', 'British Virgin Islands', 'US Virgin Islands',
                 'Democratic Republic of the Congo', 'South Korea', 'Moldova',
                 'Palestine', 'Taiwan', 'Tanzania']

    if iso_code in code_list:
        return name_list[code_list.index(iso_code)]
    else:
        return df['Country']


def get_iso_countries(cleaning_function=clean_iso):
    """All this does is scrape the table of the according Wikipedia page, and
    apply the cleaning function defined above."""

    response = requests.get('https://en.wikipedia.org/wiki/ISO_3166-2')
    soup = BeautifulSoup(response.text, 'lxml')

    table = soup.find('table', {'class': 'wikitable'})
    country_rows = Series([row.text for row in table.find_all('a')][2:])

    code_indexes = country_rows[country_rows.str.len() == 2].index

    codes = country_rows[code_indexes].reset_index(drop=True)
    names = country_rows[code_indexes + 1].reset_index(drop=True)

    codes.name = 'Code'
    names.name = 'Country'

    df = concat([codes, names], axis=1)

    df['Country'] = df.apply(cleaning_function, axis=1)

    return df, set(df['Country'])


us_states = {'AK': 'Alaska', 'AL': 'Alabama', 'AR': 'Arkansas',
             'AS': 'American Samoa', 'AZ': 'Arizona', 'CA': 'California',
             'CO': 'Colorado', 'CT': 'Connecticut',
             'DC': 'District of Columbia', 'DE': 'Delaware', 'FL': 'Florida',
             'GA': 'Georgia', 'GU': 'Guam', 'HI': 'Hawaii', 'IA': 'Iowa',
             'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'KS': 'Kansas',
             'KY': 'Kentucky', 'LA': 'Louisiana', 'MA': 'Massachusetts',
             'MD': 'Maryland', 'ME': 'Maine', 'MI': 'Michigan',
             'MN': 'Minnesota', 'MO': 'Missouri',
             'MP': 'Northern Mariana Islands', 'MS': 'Mississippi',
             'MT': 'Montana', 'NC': 'North Carolina', 'ND': 'North Dakota',
             'NE': 'Nebraska', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
             'NM': 'New Mexico', 'NV': 'Nevada', 'NY': 'New York',
             'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon',
             'PA': 'Pennsylvania',  'PR': 'Puerto Rico', 'RI': 'Rhode Island',
             'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
             'TX': 'Texas', 'UT': 'Utah', 'VA': 'Virginia',
             'VI': 'Virgin Islands', 'VT': 'Vermont', 'WA': 'Washington',
             'WI': 'Wisconsin', 'WV': 'West Virginia', 'WY': 'Wyoming'}


ca_provinces = {'AB': 'Alberta', 'BC': 'British Columbia', 'MB': 'Manitoba',
                'NB': 'New Brunswick', 'NL': 'Newfoundland and Labrador',
                'NF': 'Newfoundland and Labrador',
                'NT': 'Northwest Territories', 'NS': 'Nova Scotia',
                'NU': 'Nunavut', 'ON': 'Ontario', 'PE': 'Prince Edward Island',
                'PQ': 'Quebec', 'QC': 'Quebec', 'SK': 'Saskatchewan',
                'YT': 'Yukon', 'YK': 'Yukon'}

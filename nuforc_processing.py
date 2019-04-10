"""
This script processes the data extracted from the accompanying webscraper as
to prepare the data for exploratory and/or descriptive analysis.
@author: MoonJam
"""

import pandas as pd
import numpy as np
import nuforc_data
import geography


# Because I know I will want to work with time and text data, I will first
# get the results of my web scrape to the point that those are confidently
# ready for analysis.

ufo = nuforc_data.get(True)
iso_codes, country_set = geography.get_iso_countries()


def quantify_duration(df, result_column, pattern_dictionary):
    for pattern in pattern_dictionary:
        mask = df['Duration'].str.contains(pattern) == True
        df.loc[mask, result_column] = float(pattern_dictionary[pattern])


def parse_country(df, countries=country_set,
                  us=geography.us_states, ca=geography.ca_provinces):
    country = df['Country']
    state = df['State']

    if state in us:
        return 'United States of America'
    elif state in ca:
        return 'Canada'
    elif type(country) == str and country in countries:
        return country
    else:
        return np.nan


def relabel_shape(shape):
    lower_shape = shape.lower()
    if lower_shape in ('circle', 'round', 'sphere'):
        return 'Round'
    elif lower_shape in ('cigar', 'cylinder'):
        return 'Cylindrical'
    elif lower_shape in ('', 'unknown', 'other'):
        return 'Other'
    elif lower_shape in ('flash', 'flare'):
        return 'Flashing'
    elif lower_shape.find('chang') >= 0:
        return 'Variable'
    elif lower_shape.find('triang') >= 0:
        return 'Triangular'
    else:
        return shape

# I'm willing to drop missing date/time pairs, as well as the questionable
# "historical" observations, leaving behind 98.5% of the original.
ufo['Year'] = ufo['Source'].str.extract('((?<=ndxe)[\\d]{4})')
ufo['Time'] = ufo['Date/Time'].str.extract('([\\d]{1,2}:[\\d]{1,2})$')

ufo = ufo[ufo['Year'].notna() & ufo['Time'].notna()]
ufo = ufo[ufo['Year'].astype('int') >= 1947]

ufo['Month'] = ufo['Date/Time'].str.extract('^([\\d]{1,2})')
ufo['Day'] = ufo['Date/Time'].str.extract('((?<=/)[\\d]{1,2}(?=/))')

for column in ('Month', 'Day'):
    ufo[column] = ufo[column].str.pad(width=2, fillchar='0')

ufo['Date'] = ufo['Year'].str.cat(ufo[['Month', 'Day']], sep='/')
ufo['Date/Time'] = ufo['Date'].str.cat(ufo['Time'], sep=' ')

ufo.drop(['Date', 'Time', 'Month', 'Day', 'Year', 'Source'], axis=1,
            inplace=True)

ufo['Date/Time'] = pd.to_datetime(ufo['Date/Time'])

# MUFON's efficacy/relevance seems to be a topic of conversation within
# Ufology, and it looks like Peter marks when reports are referred by them.

ufo['MUFON Report'] = ufo['Summary'].str.contains('mufon', case=False)
ufo['Summary'].str.replace('mufon report', '', case=False)

# The main crux of any analysis of this data will hinge to some degree on the
# witness descriptions. I'm willing to cull any data that is missing or
# otherwise inappropriate, as this still leaves me with 98.47% of the data.

ufo = ufo[ufo['Summary'].notna()]

# Peter Davenport places "ufo note" to highlight several different things -
# be it blank descriptions or potential misidentification.
# Removing these brings the available data down to 94.38%, but frankly it's
# in better shape for future NLP. I'd like to better handle these later on.

annotated = ufo[ufo['Summary'].str.contains('ufo note', case=False)]
ufo = ufo[~ufo['Summary'].str.contains('ufo note', case=False)]

# The 'Summary' feature doubles as a comments section for Peter Davenport...
# some comments are more useful than others.

ufo['Summary'] = ufo['Summary'].str.replace('anonymous|report', '',
      case=False)

ufo['Summary'] = ufo['Summary'].str.replace('\\(|\\)', '')

# The following two observation types could be interesting to work with
# separately.

hoaxes = ufo[ufo['Summary'].str.contains('hoax', case=False)]
madar = ufo[ufo['Summary'].str.contains('madar', case=False)]

# At this point, we are left with 93.21% of the original dataset.
ufo = ufo[~ufo['Summary'].str.contains('hoax', case=False) &
                ~ufo['Summary'].str.contains('madar', case=False)]

# There are a very small amount whose only summary is that there is none.
ufo = ufo[ufo['Summary'].str.contains('no info', case=False) == False]

# I'm also just removing his notes, which impact about 4% of the summaries.
ufo['Summary'] = ufo['Summary'].str.replace('nuforc note.+pd', '', case=False)

# Having eliminated or put aside certain portions of the original dataset,
# duration data should be extracted and imputed into a usable form.

words = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
         'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen']

numbers = [n for n in range(1, len(words) + 1)]

units = ['ho?u?r', 'minu?t?e?s?', 'seco?n?d?s?']
values = [3600, 60, 1]

number_pats = dict(zip(words, numbers))
second_pats = dict(zip(units, values))

ufo['Seconds'] = np.nan
ufo['Value'] = ufo['Duration'].str.extract('([\\d]+)').astype('float')

for key, value in zip(['Seconds', 'Value'], [second_pats, number_pats]):
    quantify_duration(ufo, key, value)

ufo['Duration'] = ufo['Value'] * ufo['Seconds']

# Because of a pair of outliers, I will use the median to replace missing
# values for now.

median_duration = ufo['Duration'].median()
ufo['Duration'].fillna(median_duration, inplace=True)

ufo.drop(['Seconds', 'Value'], axis=1, inplace=True)

# Supporting data about the location of the sighting needs cleaning, and
# it would be helpful to try and assess the country from those that lack
# an easily identifiable American state/Canadian province.

ufo['City'] = ufo['City'].str.replace('\(.+\)', '')

country_regex = '(' + '|'.join(set(iso_codes['Country'])) + ')'

ufo['Extra'] = ufo['City'].str.title().str.extract('((?<=\().+(?=\)))')
ufo['Country'] = ufo['Extra'].str.extract(country_regex, expand=False)
ufo['State'] = ufo['State'].str.upper().str.replace('[^A-Za-z]', '')
ufo.drop('Extra', inplace=True, axis=1)

ufo['Country'] = ufo.apply(parse_country, axis=1)

# Additionally, the shape data is very messy.
ufo['Shape'] = ufo['Shape'].str.strip().str.title()

# There are a many labels that are virtually identical - I will merge them.
ufo['Shape'] = ufo['Shape'].apply(relabel_shape)

final_columns = ['Date/Time', 'Duration', 'Shape', 'City', 'State', 'Country',
                 'Summary', 'MUFON Report']

ufo = ufo[final_columns]
ufo.reset_index(inplace=True, drop=True)

ufo.to_csv('ufo_data.csv', index=False)

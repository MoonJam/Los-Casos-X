"""
A webscraper designed to obtain NUFORC's UFO sighting data and format it into
an analysis-ready format. The end result exports the data as a .csv file as to
avoid constantly requesting data from the source.

@author: MoonJam
"""

from selenium import webdriver
from bs4 import BeautifulSoup
from pandas import DataFrame


def get_soup(url, web_driver):
    web_driver.get(url)
    html_source = web_driver.page_source

    return BeautifulSoup(html_source, features='lxml')


def get_urls(web_driver):
    main_url = 'http://www.nuforc.org/webreports/'
    soup = get_soup(main_url + 'ndxevent.html', web_driver)

    tr_tags = soup.tbody.find_all('tr')
    a_tags = [tag.find_all('a') for tag in tr_tags]

    return [main_url + tag[0]['href'] for tag in a_tags]


def get_data(url, web_driver, *columns):
    soup = get_soup(url, web_driver)

    tr_tags = soup.tbody.find_all('tr')

    for table_row in tr_tags:
        row_data = table_row.find_all('td')

        for i in range(0, 7):
            columns[i].append(row_data[i].text)

        columns[7].append(url)


def get(write_csv=False):
    date, city, state, shape, duration, text, posted, source = ([], [], [], [],
                                                                [], [], [], [])

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(options=options)

    target_urls = get_urls(driver)

    for url in target_urls:
        get_data(url, driver, date, city, state, shape,
                 duration, text, posted, source)

    column_names = ['Date/Time', 'City', 'State', 'Shape', 'Duration', 'Summary',
                    'Posted', 'Source']
    column_data = [date, city, state, shape, duration, text, posted, source]

    compiled_data = dict(zip(column_names, column_data))

    nuforc = DataFrame(compiled_data)

    if write_csv:
        nuforc.to_csv('nuforc_data.csv', index=False)

    return nuforc

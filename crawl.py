from collections import defaultdict

import lxml.html
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import Select
import requests

params = {
    'Town': 'Bukit+Batok',
    'Flat_Type': 'SBF',
    'selectedTown': 'Bukit+Batok',
    'Flat': '4-Room',
    'ethnic': 'C',
    'ViewOption': '1',
    'Block': '0',
    'DesType': 'A',
    'EthnicA': '',
    'EthnicM': '',
    'EthnicC': 'C',
    'EthnicO': '',
    'numSPR': '',
    'dteBallot': '201711',
    'Neighbourhood': '',
    'Contract': '',
    'projName': '',
    'BonusFlats1': 'N',
    'searchDetails': 'Y',
    'brochure': 'false'
}

headers = {
    'Host': 'services2.hdb.gov.sg',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://services2.hdb.gov.sg/webapp/BP13AWFlatAvail/BP13EBSFlatSearch?Town=Bukit%20Batok&Flat_Type=SBF&DesType=A&ethnic=Y&Flat=4-Room&ViewOption=A&dteBallot=201711&projName=A',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

start_page = "https://services2.hdb.gov.sg/webapp/BP13AWFlatAvail/BP13EBSFlatSearch"
r = requests.get(start_page, params=params, headers=headers)
assert r.status_code == 200

page = lxml.html.fromstring(r.text)
towns = page.get_element_by_id('Town').value_options


town_blocks = {}
cookie = None

for town in towns:
    params['Town'] = town
    params['selectedTown'] = town
    start_page = "https://services2.hdb.gov.sg/webapp/BP13AWFlatAvail/BP13EBSFlatSearch"
    r = requests.get(start_page, params=params, headers=headers, cookies=None)
    cookie = r.cookies
    print(r.url)
    assert r.status_code == 200
    html_text = r.text
    if 'There is no block in this contract matching your criteria.' in html_text:
        print(town, 'no blocks')
        continue
    page = lxml.html.fromstring(html_text)
    block_lists = page.get_element_by_id('blockDetails').xpath('//div/table/tbody')
    if len(block_lists) == 0:
        continue
    blocks = block_lists[0].getchildren()[0].xpath('//td')[0].xpath('//div[1]/@onclick')
    positional_key = {1: 'block', 3: 'neighbourhood', 5: 'contract'}
    block_tuple = [{positional_key[i]: block.split("'")[i] for i in list(positional_key.keys())} for block in blocks]
    town_blocks[town] = block_tuple


driver = webdriver.Remote(
    command_executor='http://127.0.0.1:4444/wd/hub',
    desired_capabilities=DesiredCapabilities.HTMLUNITWITHJS)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome('/usr/local/bin/chromedriver', chrome_options=chrome_options)

start_page = "https://services2.hdb.gov.sg/webapp/BP13AWFlatAvail/BP13EBSFlatSearch?Town=Ang+Mo+Kio&Flat_Type=SBF&selectedTown=Ang+Mo+Kio&Flat=5-Room&ethnic=C&ViewOption=1&Block=0&DesType=A&EthnicA=&EthnicM=&EthnicC=C&EthnicO=&numSPR=&dteBallot=201711&Neighbourhood=&Contract=&projName=&BonusFlats1=N&searchDetails=Y&brochure=false"
driver.get(start_page)


def rec_dd():
    return defaultdict(rec_dd)


all_units = rec_dd()
for town in towns[3:]:
    print('looking at', town)

    select = Select(driver.find_element_by_id('Town'))
    options = select.options

    for i in range(len(options)):
        if options[i].text == town:
            print('found', options[i].text)
            select.select_by_index(i)
            break

    print('at', driver.current_url)
    select = Select(driver.find_element_by_id('Town'))
    assert select.all_selected_options[0].text == town

    flat_select = Select(driver.find_element_by_id('Flat'))
    flat_options = flat_select.options
    for i in range(len(flat_options)):
        if flat_options[i].text.strip() == '4-Room':
            print('found', flat_options[i].text)
            flat_select.select_by_index(i)
            break

    ethnic_select = Select(driver.find_element_by_id('ethnic'))
    ethnic_options = ethnic_select.options
    for i in range(len(ethnic_options)):
        if ethnic_options[i].text.strip() == 'Chinese':
            print('found', ethnic_options[i].text)
            ethnic_select.select_by_index(i)
            break

    availability_select = Select(driver.find_element_by_id('ViewOption'))
    availability_options = availability_select.options
    for i in range(len(availability_options)):
        if availability_options[i].text.strip() == 'Chinese':
            print('found', availability_options[i].text)
            availability_select.select_by_index(i)
            break

    search_btn = driver.find_element_by_id('searchButtonId')
    search_btn.click()

    table = driver.find_element_by_xpath("//div[@id='blockDetails']/div/table")
    rows = table.find_elements('tag name', 'tr')

    possible_click = []
    for row in rows:
        if row.text == "There is no block in this contract matching your criteria.":
            print(row.text)
            continue
        columns = row.find_elements('tag name', 'td')
        for td in columns:
            print(td)
            if len(td.find_elements('tag name', 'div')) <= 0:
                continue

            d = td.find_elements('tag name', 'div')[0]
            j = d.get_attribute('onclick')
            if j.startswith('checkBlk'):
                possible_click.append(j)
                print(j)

    for block in possible_click:
        print('currently looking at', block)

        table = driver.find_element_by_xpath("//div[@id='blockDetails']/div/table")
        rows = table.find_elements('tag name', 'tr')

        block_element = None
        for row in rows:
            columns = row.find_elements('tag name', 'td')
            for td in columns:
                print('at cell', td.text)
                if len(td.find_elements('tag name', 'div')) <= 0:
                    continue

                d = td.find_elements('tag name', 'div')[0]
                j = d.get_attribute('onclick')
                if j == block:
                    block_element = d
                    break

            if block_element is not None:
                break

        print('clicking on', block_element.get_attribute('onclick'))
        block_element.click()
        current_url = driver.current_url
        print(current_url)

        block_details = driver.find_element_by_id('blockDetails').find_elements_by_class_name('row')

        units = dict()
        units['block'] = block_details[1].find_elements_by_class_name('columns')[1].text.strip()
        units['street'] = block_details[1].find_elements_by_class_name('columns')[3].text.strip()
        units['completion_date'] = block_details[2].find_elements_by_class_name('columns')[1].text.strip()
        units['delivery_date'] = block_details[3].find_elements_by_class_name('columns')[1].text.strip()
        units['lease_date'] = block_details[4].find_elements_by_class_name('columns')[1].text.strip()
        units['quote'] = block_details[5].find_elements_by_class_name('columns')[1].text.strip()
        units['unit'] = []

        unit_table = block_details[6].find_elements('tag name', 'tr')

        for row in unit_table:
            print('looking at', row.text)
            assert current_url == driver.current_url
            columns = row.find_elements('tag name', 'td')
            for td in columns:
                unit = td.text.strip()
                assert unit.startswith('#')

                for e in driver.find_elements_by_class_name('tooltip'):
                    if e.get_attribute('data-selector') == unit:
                        dat = e.get_attribute('title').split('<br>')
                        price = dat[0]
                        size = dat[2]

                units['unit'].append({
                    'unit': unit,
                    'price': price,
                    'size': size.replace('\xa0', ' ')
                })

        for button in driver.find_elements_by_name('mapButton'):
            js = button.get_attribute('onclick').strip()
            print('got button with attribute', js)
            if 'townMap' in js:
                button.click()
                img = driver.find_element_by_id('sbfTownImg').get_attribute('src')
                units['townMap'] = img

            if 'sitePlan' in js:
                button.click()
                img = driver.find_element_by_id('vendor1').get_attribute('src')
                units['sitePlan'] = img

        print('# of units', len(units['unit']))
        all_units[town][block] = units

driver.close()

import csv

fieldnames = ['town', 'block', 'street', 'completion_date', 'delivery_date', 'lease_date', 'quote', 'unit', 'price',
              'size', 'townMap', 'sitePlan']

csvfile = open('units2.csv', 'w')
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
writer.writeheader()
for k, v in all_units.items():
    town = k
    for k2, v2 in v.items():
        block = v2['block']
        street = v2['street']
        completion_date = v2['completion_date']
        delivery_date = v2['delivery_date']
        lease_date = v2['lease_date']
        quote = v2['quote']
        townMap = v2.get('townMap')
        sitePlan = v2.get('sitePlan')
        for u in v2['unit']:
            d = {'town': town, 'block': block, 'street': street, 'completion_date': completion_date,
                 'delivery_date': delivery_date, 'lease_date': lease_date, 'quote': quote, 'unit': u['unit'],
                 'price': u['price'], 'size': u['size'], 'townMap': townMap, 'sitePlan': sitePlan}
            writer.writerow(d)
csvfile.close()
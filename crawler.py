"""
Script monitors www.otomoto.pl - a Polish car sales ad website.
It finds and stores all car dealers located in 50km radius from Poznań and
car sales offers published by those dealers.
"""

import collections
import datetime
import io
import json
import os
import time

from bs4 import BeautifulSoup
import requests
import jinja2

BASE_URL = (
    'https://www.otomoto.pl/'
    'osobowe/poznan/?search%5Bdist%5D=50'
)

PARSER_LIBRARY = 'html.parser'
TIME_FORMAT = '%d.%m.%Y, %H:%M:%S'

OFFERS_FILE_NEW = 'offers_list_new.json'
OFFERS_FILE_OLD = 'offers_list_old.json'

FILEPATH_FILE_NEW = os.path.join('crawl_reports', OFFERS_FILE_NEW)
FILEPATH_FILE_OLD = os.path.join('crawl_reports', OFFERS_FILE_OLD)


def main_page_links(main_soup):
    """
    Creates pagination links for main page.
    """
    print('(START) Creating pagination links for main page.')
    start_time = time.time()

    pagination_links = [BASE_URL]

    pagination = main_soup.find('ul', class_='om-pager rel')
    pagination_elements = pagination.find_all('li', class_='')
    last_pagination_element = pagination_elements[-1].get_text()
    total_pages_count = int(last_pagination_element.strip())

    for page_number in range(2, total_pages_count + 1):
        link = '{}&page={}'.format(BASE_URL, page_number)
        pagination_links.append(link)

    end_time = round((time.time() - start_time), 2)
    print('FINISHED after {} sec.\n'.format(end_time))

    return pagination_links


def crawl_all_pages(pages_links):
    """
    Crawls all main pages and gets dealers shop links.
    """
    print('(START) Getting dealers shop links.')
    start_time = time.time()

    dealers_shop_links = []
    for link in pages_links:
        page_response = requests.get(link)
        page_soup = BeautifulSoup(page_response.content, PARSER_LIBRARY)

        # Getting links to dealers shop
        dealer_class = 'has-feature-shop'
        dealers_offers = page_soup.find_all('article', class_=dealer_class)

        for offer in dealers_offers:
            class_identifier = 'offer-item__link-seller in-content'
            links = offer.find('a', class_=class_identifier).get('href')

            if links not in dealers_shop_links:
                dealers_shop_links.append(links)

    end_time = round((time.time() - start_time), 2)
    print('FINISHED after {} sec.\n'.format(end_time))

    return dealers_shop_links


def get_dealers_info(dealers_shop_links):
    """
    Gets info about dealers - name and list of links of pages with offers.
    """
    print('(START) Getting information about all dealers.')
    start_time = time.time()

    dealers = {}
    for dealer_id, link in enumerate(dealers_shop_links):
        dealer_response = requests.get(link)
        dealer_soup = BeautifulSoup(dealer_response.content, PARSER_LIBRARY)
        dealer_name_element = dealer_soup.find('div', class_='dealer-title')

        if not dealer_name_element:
            continue

        dealer_name = dealer_name_element.get_text().split()

        # Genereting links for all pages with dealer offers
        dealer_pagination = dealer_soup.find('ul', class_='om-pager rel')
        if dealer_pagination:
            if len(dealer_pagination) > 1:
                dealer_page_count = dealer_pagination.find_all('li', class_='')
            else:
                dealer_page_count = dealer_pagination.find('li', class_='')

            page_count = dealer_page_count[-1].get_text().strip()
            total_offers_pages_count = int(page_count)

            dealers_pages = [link]
            for page in range(2, total_offers_pages_count + 1):
                links = '{}/shop/?page={}'.format(link, page)
                dealers_pages.append(links)
        else:
            dealers_pages = [link]

        # Collecting info about all dealers
        dealers[dealer_id] = {
            'dealer_name': ' '.join(dealer_name),
            'dealers_pages': dealers_pages,
        }

    end_time = round((time.time() - start_time), 2)
    print('FINISHED after {} sec.\n'.format(end_time))

    return dealers


def get_dealers_offers(dealers):
    """
    Gets information about all dealers offers - id, URL, car name, dealer name,
    collected date.
    """
    print('(START) Getting information about dealers offers.')
    start_time = time.time()

    offers = {}
    for dealer_id in dealers:
        for link in dealers[dealer_id]['dealers_pages']:
            offer_response = requests.get(link)
            offer_soup = BeautifulSoup(offer_response.content, PARSER_LIBRARY)

            offer_info = offer_soup.find_all('a', class_='offer-title__link')
            if not offer_info:
                continue

            # Collecting info about each offer
            price_class = 'offer-price__number'
            offer_price = offer_soup.find('span', class_=price_class)
            for info in offer_info:
                offer_id = info['data-ad-id']
                offer_link = info['href']
                car_name = info['title']
                dealer_name = dealers[dealer_id].get('dealer_name')
                price = offer_price.get_text().split()

                collected_date = str(
                    datetime.datetime.now().strftime(TIME_FORMAT)
                )

                offers[offer_id] = {
                    'offer_link': offer_link,
                    'car_name': car_name,
                    'dealer_name': dealer_name,
                    'offer_price': ' '.join(price),
                    'collected_data': collected_date,
                }

    end_time = round((time.time() - start_time), 2)
    print('FINISHED after {} sec.\n'.format(end_time))

    return offers


def save_json_file(data_to_save, filename):
    """
    Saves data into JSON file.
    """

    if not os.path.isdir('crawl_reports'):
        os.makedirs('crawl_reports')

    filepath = os.path.join('crawl_reports', filename)
    with io.open(filepath, 'w', encoding='utf8') as outfile:
        offer_info = json.dumps(
            data_to_save,
            indent=4,
            sort_keys=True,
            separators=(',', ': '),
            ensure_ascii=False
        )
        outfile.write(offer_info)


def save_html_file(data_to_render, template, filename):
    """
    Generates an HTML file using a template with Jinja2.
    """

    templates_path = os.path.join('templates', template)
    with io.open(templates_path, 'r', encoding='utf8') as template_file:
        template = jinja2.Template(template_file.read())
        render_template = template.render(
            data=data_to_render
        )

    html_table = os.path.join('crawl_reports', filename)
    with io.open(html_table, 'w', encoding='utf8') as outfile:
        outfile.write(render_template)


def find_sold_cars():
    """
    Detects which car was sold.
    """
    print('(START) Detecting which car was sold.')
    start_time = time.time()

    with open(FILEPATH_FILE_NEW) as new:
        new_data = json.load(new)

    with open(FILEPATH_FILE_OLD) as old:
        old_data = json.load(old)

    sold_cars = set(old_data).difference(set(new_data))

    sold_cars_data = {offer_id: old_data[offer_id] for offer_id in sold_cars}

    save_json_file(sold_cars_data, 'sold_cars.json')

    all_cars = dict(old_data, **new_data)
    sold_date = str(datetime.datetime.now().strftime(TIME_FORMAT))

    render_data = {
        'all_cars': all_cars,
        'sold_cars': sold_cars_data,
        'sold_date': sold_date,
    }

    save_html_file(render_data, 'cars_offers.html', 'offers.html')

    end_time = round((time.time() - start_time), 2)
    print('FINISHED after {} sec.\n'.format(end_time))


def total_sum_of_cars_price():
    """
    Sums up car prices for relevant car model.
    """
    print('(START) Summing up car prices for relevant car model.')
    start_time = time.time()

    with open(FILEPATH_FILE_NEW) as new:
        new_data = json.load(new)

    results = collections.defaultdict(float)

    for car_data in new_data.values():
        price = car_data['offer_price'][:-4].replace(',', '.')
        car_price = float(price.replace(' ', ''))

        results[car_data['car_name']] += car_price

    save_json_file(results, 'cars.json')
    save_html_file(results, 'cars_info.html', 'cars.html')

    end_time = round((time.time() - start_time), 2)
    print('FINISHED after {} sec.'.format(end_time))


if __name__ == '__main__':
    print('\n=================================================')
    print(
        'SCRIPT STARTS at {}\n'.format(
            datetime.datetime.now().strftime(TIME_FORMAT)
        )
    )

    response = requests.get(BASE_URL)
    soup_data = BeautifulSoup(response.content, PARSER_LIBRARY)

    main_page_links_data = main_page_links(soup_data)
    crawl_data = crawl_all_pages(main_page_links_data)
    dealers_info = get_dealers_info(crawl_data)
    all_offers = get_dealers_offers(dealers_info)

    print('Saving all data into JSON file.\n')
    if os.path.isfile(FILEPATH_FILE_NEW):
        os.rename(FILEPATH_FILE_NEW, FILEPATH_FILE_OLD)

    save_json_file(all_offers, OFFERS_FILE_NEW)

    dealers_list = os.path.join('crawl_reports', 'dealers_list.txt')
    with io.open(dealers_list, 'w', encoding='utf8') as dealers_info_file:
        dealers_info_file.write(
            'Car dealers located in 50km radius from Poznań:\n'
        )
        for dealer_id in dealers_info:
            dealers_info_file.write(
                '\n\t{}: {}\n'.format(
                    dealer_id,
                    dealers_info[dealer_id]['dealer_name']
                )
            )

    if os.path.isfile(FILEPATH_FILE_NEW) and os.path.isfile(FILEPATH_FILE_OLD):
        find_sold_cars()

    if os.path.isfile(FILEPATH_FILE_NEW):
        total_sum_of_cars_price()

    print(
        '\nSCRIPT ENDED at {}'.format(
            datetime.datetime.now().strftime(TIME_FORMAT)
        )
    )
    print('=================================================\n')

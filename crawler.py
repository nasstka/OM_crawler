import json
import io
import os
import collections
import datetime
import requests

import jinja2

from bs4 import BeautifulSoup

BASE_URL = 'https://www.otomoto.pl/osobowe/poznan/'

# Offers located in 50km radius from Poznań
main_page_link = "{}?search%5Bdist%5D=50&search%5Bcountry%5D=".format(BASE_URL)
response = requests.get(main_page_link)
soup = BeautifulSoup(response.content, 'html.parser')

# Get total page count on main page
pagination = soup.find('ul', class_='om-pager rel')
pagination_number = pagination.find_all('li', class_='')
total_pages_count = int(
    pagination_number[-1].get_text().strip()
    )

# Generete links for all pages
pages_links = [main_page_link]
page_link = 'https://www.otomoto.pl/osobowe/poznan/?search%5Bdist%5D=50&search%5Bcountry%5D=&page='

# Low page count for test, change to total_pages_count + 1 to crawl all pages
for page_number in range(2, 4):
    link = '{}{}'.format(page_link, page_number)
    pages_links.append(link)

# Crawl all pages
for page in pages_links:
    page_response = requests.get(page)
    page_soup = BeautifulSoup(page_response.content, 'html.parser')

    # Get links to dealers shop
    dealers_offers = page_soup.find_all('article', class_='has-feature-shop')

    dealers_shop_links = []
    for offer in dealers_offers:
        class_identifier = 'offer-item__link-seller in-content'
        links = offer.find('a', class_=class_identifier).get('href')

        if links not in dealers_shop_links:
            dealers_shop_links.append(links)


# Get info about dealers
dealers = {}

# Temporary dealers ids
dealer_id = 0
for dealer in dealers_shop_links:
    dealer_response = requests.get(dealer)
    dealer_soup = BeautifulSoup(dealer_response.content, 'html.parser')

    dealer_name = dealer_soup.find('div', class_='dealer-title').get_text()

    # Generete links for all pages with offers
    dealer_offers_pagination = dealer_soup.find('ul', class_='om-pager rel')

    dealers_pages = [dealers_shop_links[dealer_id]]

    if dealer_offers_pagination is not None:
        if len(dealer_offers_pagination) > 1:
            dealer_offers_number = dealer_offers_pagination.find_all(
                'li',
                class_=''
            )
        else:
            dealer_offers_number = dealer_offers_pagination.find(
                'li',
                class_=''
            )

        total_offers_pages_count = int(
            dealer_offers_number[-1].get_text().strip()
        )

        for page in range(2, total_offers_pages_count + 1):
            link = '{}/shop/?page={}'.format(
                dealers_shop_links[dealer_id],
                page
            )
            dealers_pages.append(link)
    else:
        dealers_pages = [dealers_shop_links[dealer_id]]

    # Collecting info about all dealers
    dealers[dealer_id] = {
        'dealer_name': dealer_name.strip(),
        'dealer_link': dealers_shop_links[dealer_id],
        'dealers_pages': dealers_pages,
    }
    dealer_id += 1

# Get all dealers offers
offers = {}
for key in dealers:
    for link in dealers[key]['dealers_pages']:
        offer_response = requests.get(link)
        offer_soup = BeautifulSoup(offer_response.content, 'html.parser')

        offer_info = offer_soup.find_all('a', class_='offer-title__link')

        # Collect main info about each offer
        for info in offer_info:
            offer_id = info['data-ad-id']
            offer_link = info['href']
            car_name = info['title']
            offers[offer_id] = {
                'offer_link': offer_link,
                'car_name': car_name,
                'dealer_name': dealers[key].get('dealer_name'),
                'offer_price': ' '.join(offer_soup.find('span', class_='offer-price__number').get_text().split()),
                'collected_data': str(datetime.datetime.now().strftime('%d.%m.%Y, %H:%M:%S')),
            }

if not os.path.isdir('data'):
    os.makedirs('data')

if os.path.isfile(os.path.join('data', 'offers_list_new.json')):
    os.rename(os.path.join('data', 'offers_list_new.json'), os.path.join('data', 'offers_list_old.json'))
    with io.open(os.path.join('data', 'offers_list_new.json'), 'w', encoding='utf8') as outfile:
        offer_info = json.dumps(
            offers,
            indent=4,
            sort_keys=True,
            separators=(',', ': '),
            ensure_ascii=False
        )
        outfile.write(offer_info)

else:
    with io.open(os.path.join('data', 'offers_list_new.json'), 'w', encoding='utf8') as outfile:
        offer_info = json.dumps(
            offers,
            indent=4,
            sort_keys=True,
            separators=(',', ': '),
            ensure_ascii=False
        )
        outfile.write(offer_info)

if os.path.isfile(os.path.join('data', 'offers_list_new.json')) and os.path.isfile(os.path.join('data', 'offers_list_old.json')):
    with open('data/offers_list_new.json') as new:
        new_data = json.load(new)

    with open('data/offers_list_old.json') as old:
        old_data = json.load(old)


    sold_cars = set(old_data).difference(set(new_data))

    sold_cars_data = {offer_id: old_data[offer_id] for offer_id in sold_cars}

    with io.open(os.path.join('data', 'sold_cars.json'), 'w', encoding='utf8') as outfile:
        sold_cars_info = json.dumps(
            sold_cars_data,
            indent=4,
            sort_keys=True,
            separators=(',', ': '),
            ensure_ascii=False
        )
        outfile.write(sold_cars_info)

    all_cars = dict(old_data, **new_data)
    sold_date = str(datetime.datetime.now().strftime('%d.%m.%Y, %H:%M:%S'))

    with io.open(os.path.join('templates', 'cars_offers.html'), 'r', encoding='utf8') as template_file:
        template = jinja2.Template(template_file.read())
        render_template = template.render(offer_data=all_cars, sold=sold_cars_data, sold_date=sold_date)

    with io.open(os.path.join('data', 'offers.html'), 'w', encoding='utf8') as outfile:
        outfile.write(render_template)

# Sold cars
if os.path.isfile('data/offers_list_new.json'):
    with open('data/offers_list_new.json') as new:
        new_data = json.load(new)

    results = collections.defaultdict(int)

    for car_data in new_data.values():
        car_price = int(car_data['offer_price'][:-4].replace(' ', ''))

        results[car_data['car_name']] += car_price

    with io.open(os.path.join('data', 'cars.json'), 'w', encoding='utf8') as outfile:
        cars_info = json.dumps(
            results,
            indent=4,
            sort_keys=True,
            separators=(',', ': '),
            ensure_ascii=False
        )
        outfile.write(cars_info)


    with io.open(os.path.join('templates', 'cars_info.html'), 'r', encoding='utf8') as template_file:
        template = jinja2.Template(template_file.read())
        render_template = template.render(data=results)

    with io.open(os.path.join('data', 'cars.html'), 'w', encoding='utf8') as outfile:
        outfile.write(render_template)

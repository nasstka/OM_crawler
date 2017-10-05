import requests

from bs4 import BeautifulSoup

# Offers located in 50km radius from Poznań
main_page_link = "https://www.otomoto.pl/osobowe/poznan/?search%5Bdist%5D=50&search%5Bcountry%5D="
response = requests.get(main_page_link)
soup = BeautifulSoup(response.content, 'html.parser')

# Get total page count on main page
pagination = soup.find('ul', class_='om-pager rel')
pagination_number = pagination.find_all('li', class_='')
total_pages_count = int(
    pagination_number[-1].get_text().strip()
    )

# Generete links for all pages
pages_links = [
    main_page_link,
]
page_link = 'https://www.otomoto.pl/osobowe/poznan/?search%5Bdist%5D=50&search%5Bcountry%5D=&page='

# Low page count for test, change to total_pages_count + 1 to crawl all pages
for page_number in range(2, 5):
    link = '{}{}'.format(page_link, page_number)
    pages_links.append(link)

# Crawl all pages
# for page in pages_links:
#     page_response = requests.get(page)
#     page_soup = BeautifulSoup(page_response.content, 'html.parser')

# For tests just one page
page_response = requests.get(pages_links[0])
page_soup = BeautifulSoup(page_response.content, 'html.parser')

# Get links to dealers shop
dealers_offers = page_soup.find_all('article', class_='has-feature-shop')

dealers_shop_links = []
for offer in dealers_offers:
    links = offer.find(
        'a',
        class_='offer-item__link-seller in-content'
    ).get('href')
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

    dealers_pages = [dealers_shop_links[dealer_id],]

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
            offers[offer_id] = {
                'offer_link': offer_link,
                'dealer_name': dealers[key].get('dealer_name')
            }

# Collect more info about each offer
for key in offers:
    offers_details = {}
    offer = offers[key].get('offer_link')
    offer_detail = requests.get(offer)
    offer_detail_soup = BeautifulSoup(offer_detail.content, 'html.parser')

    offer_price = offer_detail_soup.find(
        'span',
        class_='offer-price__number'
    ).get_text().split()
    car_name = offer_detail_soup.find(
        'h1',
        class_='offer-title'
    ).get_text().strip()
    collected_date = offer_detail_soup.find(
        'span',
        class_='offer-meta__value'
    ).get_text()

    offers_details['car_price'] = ' '.join(offer_price)
    offers_details['car_name'] = car_name
    offers_details['collected_date'] = collected_date

    offers[key].update(offers_details)

Script monitors www.otomoto.pl - a Polish car sales ad website.It finds and stores 
all car dealers located in 50km radius from Poznań and car sales offers published 
by those dealers.

OTOMOTO.pl crawler setup guide:
1. Create and activate virtualenv (with python3.6)
2. pip install -r requirements.txt
3. Run a script

Crawl reports:
1. offers_list_new.json, offers_list_old.json - list of all offers published by dealers.
2. cars.json - list of all scrapped cars and a sum of total car prices for relevant car model.
3. sold_cars.json - list of sold cars.
4. cars.html, offers.html - collected data presented in html table.
5. dealers_list.txt - list of all car dealers located in 50km radius from Poznań.
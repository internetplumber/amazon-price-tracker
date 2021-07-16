#!/usr/bin/python3

#
# Watch for price changes in a product on Amazon.
#
# Screen scraping comes from https://github.com/learningdollars/mrajab-amzn-price-tracker
# Added logic to save prices into a json file, then load them the next
# time to compare.  Could do with a lot more error handling.

import requests
import re
import pickle
import json
import os
from bs4 import BeautifulSoup

products = [
    "https://www.amazon.co.uk/Govee-Thermometer-Hygrometer-Temperature-Greenhouse/dp/B086YYL439/ref=sr_1_11?dchild=1&keywords=govee&qid=1626431269&sr=8-11&th=1",
    "https://www.amazon.co.uk/Govee-Thermometer-Hygrometer-Temperature-Greenhouse/dp/B08XQD8MFZ/ref=sr_1_11?dchild=1&keywords=govee&qid=1626431269&sr=8-11&th=1" ]

productPrices = {}
dbFileName = "prices.json"
dbOldFileName = "prices-old.json"

def get_converted_price(price):
    converted_price = float(re.sub(r"[^\d.]", "", price))
    return converted_price


def extract_url(url):
    if url.find("www.amazon.co.uk") != -1:
        index = url.find("/dp/")
        if index != -1:
            index2 = index + 14
            url = "https://www.amazon.co.uk" + url[index:index2]
        else:
            index = url.find("/gp/")
            if index != -1:
                index2 = index + 22
                url = "https://www.amazon.co.uk" + url[index:index2]
            else:
                url = None
    else:
        url = None
    return url


def get_product_details(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0"
    }
    details = {"name": "", "price": 0, "deal": True, "url": ""}
    _url = extract_url(url)
    if _url is None:
        details = None
    else:
        page = requests.get(_url, headers=headers)
        soup = BeautifulSoup(page.content, "html5lib")
        title = soup.find(id="productTitle")
        price = soup.find(id="priceblock_dealprice")
        if price is None:
            price = soup.find(id="priceblock_ourprice")
            details["deal"] = False
        if title is not None and price is not None:
            details["name"] = title.get_text().strip()
            details["price"] = get_converted_price(price.get_text())
            details["url"] = _url
        else:
            details = None
    return details

dbReadFH = open(dbFileName, 'r')
lastProdPrices = json.load(dbReadFH)
dbReadFH.close()

numProducts = len(products)
for prodIdx in range (0, numProducts):
    prodDetails = get_product_details(products[prodIdx])
    productPrices[prodDetails["url"]] = prodDetails

for prodURL in productPrices.keys():
    if prodURL in lastProdPrices.keys():
        oldPrice = lastProdPrices[prodURL]['price']
        newPrice = productPrices[prodURL]['price']
        if oldPrice != newPrice:
            print(productPrices[prodURL]['name'])
            print(productPrices[prodURL]['url'])
            if oldPrice < newPrice:
             print("Price rise!")
            elif newPrice > oldPrice:
             print("Price drop!")
            print("Last price: " + str(lastProdPrices[prodURL]['price']))
            print("New price:  " + str(productPrices[prodURL]['price']))

os.rename(dbFileName, dbOldFileName)
dbFH = open(dbFileName, 'w')
json.dump(productPrices, dbFH, indent=2)
dbFH.close()


#!/usr/bin/python3

#
# Watch for price changes in a product on Amazon.
#
# Screen scraping comes from https://github.com/learningdollars/mrajab-amzn-price-tracker
# Added logic to save prices into a json file, then load them the next
# time to compare.  Could do with a lot more error handling.

# Requires a directory AmazonPriceCheck in a user's home directory.  Feel free
# to change this to a name of your choosing by editing priceCheckDir.  Inside
# that are two files containing the last and current price run (which are
# generated automatically), and a list of products to check.
#
# products.json is just a list of URLs of Amazon products, e.g.:
# [
#   "https://www.amazon.co.uk/Govee-Thermometer-Hygrometer-Temperature-Greenhouse/dp/B086YYL439/",
#   "https://www.amazon.co.uk/Govee-Thermometer-Hygrometer-Temperature-Greenhouse/dp/B08XQD8MFZ/"
# ]
#
# This is currently very UK-specific. It uses the GBP symbol to look for the
# price, and normalises URLs based on amazon.co.uk.

import random
import requests
import re
import json
import os
from bs4 import BeautifulSoup

userAgents = [ "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.47",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36" ]

productPrices = {}
lastProdPrices = {}
homeDir = os.path.expanduser("~")
priceCheckDir = "AmazonPriceCheck"
pricePath = os.path.join(homeDir, priceCheckDir)
dbFileName = os.path.join(pricePath, "prices.json")
dbOldFileName = os.path.join(pricePath, "prices-old.json")
productFileName = os.path.join(pricePath, "products.json")

productFile = open(productFileName, "r")
products = json.load(productFile)
productFile.close


def get_converted_price(price):
    # This function has got a bit ugly as the primary id we're now using to
    # get the prices returns the price twice, so the first thing we need to
    # look for is exactly one copy of it -- note this keys on the GBP symbol
    # and should look for other currency symbols.
    price1 = re.search("£[\d,.]+", price)
    # Now we strip anyghing else our.  This is a hangover from the previous
    # way the function works, and practically all it is doing now is stripping
    # out the comma when the price is £1,000 or over.
    converted_price = float(re.sub(r"[^\d.]", "", price1.group(0)))
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
    # ToDo: add a few different User-Agent strings that can be tried at random
    # to try and avoid captchas because we look like the robot that we are.
    headers = {
        "User-Agent": random.choice(userAgents)
    }
    details = {"name": "", "price": 0, "deal": True, "url": ""}
    _url = extract_url(url)
    if _url is None:
        details = None
    else:
        page = requests.get(_url, headers=headers)
        soup = BeautifulSoup(page.content, "html5lib")
        title = soup.find(id="productTitle")
        priceLocators = [ "corePrice_feature_div"]
        for priceId in priceLocators:
            price = soup.find(id=priceId)
            if price is not None:
                break
        if price is None:
            # Can't locate a price, see what the webpage says (it's
            # probably Amazon checking we're not a robot)...
            print("Unable to get price for " + url)
            #print(page.content)
        if title is not None and price is not None:
            details["name"] = title.get_text().strip()
            details["price"] = get_converted_price(price.get_text())
            details["url"] = _url
        else:
            details = None
    return details

# Now the body of the script.  First of all, open the previous price date,
# stored in JSON format.
try:
    dbReadFH = open(dbFileName, 'r')
    lastProdPrices = json.load(dbReadFH)
    dbReadFH.close()
except:
    print("No old prices found, assuming first run.")

# Get the product details for each of items we want to track.
numProducts = len(products)
for prodIdx in range (0, numProducts):
    prodDetails = get_product_details(products[prodIdx])
    if prodDetails is not None:
        productPrices[prodDetails["url"]] = prodDetails
    else:
        url = extract_url(products[prodIdx])
        if lastProdPrices[url] is not None:
            productPrices[url] = lastProdPrices[url]
        print("Unable to get product details for " + products[prodIdx])

for prodURL in productPrices.keys():
    if prodURL in lastProdPrices.keys():
        oldPrice = lastProdPrices[prodURL]['price']
        newPrice = productPrices[prodURL]['price']
        if oldPrice != newPrice:
            print(productPrices[prodURL]['name'])
            print(productPrices[prodURL]['url'])
            if oldPrice < newPrice:
                print("Price rise!")
            elif newPrice < oldPrice:
                print("Price drop!")
            print("Last price: £" + format(lastProdPrices[prodURL]['price'], '.2f'))
            print("New price:  £" + format(productPrices[prodURL]['price'], '.2f'))
    else:
        print("New product found!")
        print(productPrices[prodURL]['name'])
        print("£" + format(productPrices[prodURL]['price'], '.2f'))

try:
    os.rename(dbFileName, dbOldFileName)
except Exception:
    pass

# Dump the new prices as JSON ready for next time.
dbFH = open(dbFileName, 'w')
json.dump(productPrices, dbFH, indent=2)
dbFH.close()

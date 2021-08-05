# Amazon Price Tracker

This script will scrape the prices of products from amazon.co.uk, save
them, and the next time it is run it will compare the prices and let you
know if they've dropped or risen.  There is no output if the price
hasn't changed.

Uses a directory "AmazonPriceCheck" to store state and list products,
this can be esaily changed in the source code.

Requires python3 and BeautifulSoup4.

Forked from https://github.com/learningdollars/mrajab-amzn-price-tracker

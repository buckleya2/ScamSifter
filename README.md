# ScamSifter
## a better way to view craigslist housing

ScamSifter is a command line tool that will sift through craigslist housing posts, remove likely scam posts, and send email alerts

Note: Scam Sifter is a personal project, meant for educational purposes only.

## Installation Instructions

Install miniconda: http://docs.conda.io/en/latest/miniconda.html

Install requirements: 
```pip3 install -r requirements.txt```

Install ScamSifter: 
```python setup.py install```

In addition to these requirements, ScamSifter requires Google maps and Gmail API tokens
- Google static maps API: https://developers.google.com/maps/documentation/geocoding/star
- Gmail API: https://developers.google.com/gmail/api/guides

## Inputs

two inputs must be specified in parameters.py before running ScamSifter

1. SEARCH_STEMS: a craigslist housing search URL with your desired filters
  - example: https://portland.craigslist.org/search/apa?bundleDuplicates=1&hasPic=1&housing_type=6&maxSqft=2200&max_price=4000&min_bathrooms=2&min_bedrooms=2
2. SCAM_KEYWORDS: a set of keywords used to identify likely scam posts
 - in this example, I used phrases such as 'rent to own' or 'realtor'
 - posts will be removed if they contain *any* of the specified keywords

four inputs must be specified when running ScamSifter

1. a directory to store output files
  - folders created by ScamSifter are PATH/database and PATH/logs
  - ScamSifter looks in PATH/database for a file called ```listing.database.txt``` This is a .txt file containing craigslist listing IDs for listings previously queried. If this file doesn't exist, ScamSifter will create a new one.
  - Without a database file, ScamSifter will search *all* craigslists postings in your specified search query, with a databse file it will only search new postings

2. path to a .txt file with a Google maps API token

3. path to a Gmail API .json credentials file

4. the email address to send email alerts to
  - by deafult, ScamSifter is configured to send emails from the Gmail account configured with the Gmail API credentials

Example command line usage

```ScamSifter /PATH/TO/OUTPUT /PATH/TO/MAPS_API /PATH/TO/GMAIL_API/token.json EMAIL_ADDRESS```


## Outputs

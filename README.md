# ScamSifter
## a better way to view craigslist housing

ScamSifter is a command line tool that will sift through craigslist housing posts, remove likely scam posts, and send email alerts

Note: Scam Sifter is a personal project, meant for educational purposes only.

## Installation Instructions

First install miniconda http://docs.conda.io/en/latest/miniconda.html

Requirements can be installed using
```pip3 install -r requirements.txt```

ScamSifter can be installed using
```python setup.py install```

In addition to these requirements, ScamSifter requires Google maps and Gmail API tokens
- Google static maps API: https://developers.google.com/maps/documentation/geocoding/star
- Gmail API: https://developers.google.com/gmail/api/guides

## Inputs

- a base craigslist housing search result stem
  - example: ```https://portland.craigslist.org/search/apa?bundleDuplicates=1&hasPic=1&housing_type=6&maxSqft=2200&max_price=4000&min_bathrooms=2&min_bedrooms=2'```
- a directory to store output files



Example command line usage

```ScamSifter /PATH/TO/OUTPUT /PATH/TO/MAPS_API /PATH/TO/GMAIL_API/token.json EMAIL_ADDRESS```


## Outputs

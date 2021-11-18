# define craigslist search URLs for searches of interest
# all searches defined here will be used
SEARCH_STEMS={'portland_house' : 'https://portland.craigslist.org/search/apa?bundleDuplicates=1&hasPic=1&housing_type=6&maxSqft=2200&max_price=4000&min_price=2000&min_bathrooms=2&min_bedrooms=2',
               'seattle_house' : 'https://seattle.craigslist.org/search/apa?bundleDuplicates=1&hasPic=1&housing_type=6&maxSqft=2200&max_price=4000&min_price=2000&min_bathrooms=2&min_bedrooms=2'}

# list of keywords to searc for in listing text that indicate a scam
SCAM_KEYWORDS=['lease to own',
               'rent to own',
               'real estate agent',
               'purchase program',
               'realtor',
               'loftium']

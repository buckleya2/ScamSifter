import requests
from email.mime.image import MIMEImage

def parse_address(json) -> list:
    """
    Function that parses the Google maps API json output 
    
    @param json: Google's reverse lookup json object
    @returns: a list with address, zipcode, neighborhood, and locality (Google defined)
    """
    result=json['results'][0]
    address=result['formatted_address']
    zipcode, neighborhood, locality=(None, None, None)
    for entry in result['address_components']:
        if 'postal_code' in entry['types']:
            zipcode=entry['long_name']
        elif 'neighborhood' in entry['types']:
            neighborhood=entry['long_name']
        elif 'locality' in entry['types']:
            locality = entry['long_name']
    return([address, zipcode, neighborhood, locality])

def reverse_lookup(key: str, lat: str, long: str) -> list:
    """
    Function that uses Google's reverse lookup API to turn latitude and longitude into a street address

    @param lat: latitude
    @param long: longitude
    @returns: Google's reverse lookup json object
    """
    # Google's reverse lookup API
    url='https://maps.googleapis.com/maps/api/geocode/json?latlng='
    r=requests.get(url + lat + ',' + long + "&key=" + key)
    json=r.json()
    # parse output
    address=parse_address(json)
    return(address)

def get_map(lat: str, long: str, api_key: str) -> MIMEImage:
    """
    Function to create a Google static map from a latitude, longitude pair
    
    @param lat: latitude
    @param long: longitude
    @param api: google maps API key
    @returns: a MIMEImage object of a Google map PNG
    """
    # set parameters to create google map
    url = 'https://maps.googleapis.com/maps/api/staticmap?'
    center_lat=str(lat)
    center_long=str(long)
    zoom=10
    r=requests.get(url, params={'center': center_lat + ',' + center_long,
                             'zoom': str(zoom),
                             'size': "200x200",
                             'markers':  center_lat + ',' + center_long,
                            'key': api_key})
    if r.status_code == 200:
        image=MIMEImage(r.content)
    else:
        image=None
    return(image)

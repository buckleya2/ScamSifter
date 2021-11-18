import bs4
import datetime
import emoji
import numpy as np
import os
import pandas as pd
import re
import requests
import time

from ScamSifter.helpers import *
from ScamSifter.maps import *
from ScamSifter.email import *

def scrape_data(url_list: list)-> dict:
    """
    Function that takes in a list of URLs and pulls data from craigslist with a sleep timer from 2-10 seconds
    
    @param url_list: list of craigslist post URLs to scrape
    @returns: a dictionary with URL as key and BeautifulSoup object as the value
    """
    soup_dict={}
    scrape_count=0
    for url in url_list:
        req=requests.get(url)
        content=req.text
        soup=bs4.BeautifulSoup(content)
        soup_dict[url]=soup
        time.sleep(np.random.randint(2,10))
        scrape_count+=1
        if scrape_count % 10 == 0:
            print("%s listings completed / %s total" % (scrape_count, len(url_list)))
    return(soup_dict)

def extract_links(soup_list: list) -> dict:
    """
    Function that extracts individual craiglist posting URLs from a craiglist search URL
    
    @param soup_list: a list of BeautifulSoup objects scraped from craigslist search URLs
    @returns: a dict with the posting ID as the key and posting URL as value
    """
    url_dict={}
    links=[re.findall(r'http[s]?:.*apa.*html', str(soup)) for soup in soup_list]
    flat_links=list(set([item for sublist in links for item in sublist]))
    for link in flat_links:
        url_dict[link.split('/')[-1].split('.')[0]]=link
    return(url_dict)

def search_links(stem: str, database: list) -> dict:
    """
    Function that pulls all individual craigslist post URLs from a base craigslist housing search result
    
    @param stem: a base craiglist URL describing a rental search
    @param database: a list of all CL post ids currently in text database
    @returns:
    """
    # scrape first results page to determine max results
    CL_dict=scrape_data([stem])
    soup=CL_dict[stem]
    max_res=int(get_first(soup.findAll('span', {'class' : 'total'})))
    
    # if multiple pages, get all search result urls
    additional_urls=generate_search_urls(stem, max_res)
    all_urls=[stem] + additional_urls

    # scrape search pages, and extract all listing urls 
    CL_dict_add=scrape_data(all_urls)
    soup_list=list(CL_dict_add.values())
    listing_dict=extract_links(soup_list)
    new_urls=check_new(database, listing_dict)
    return(new_urls)

def get_and_resize_image(soup: bs4.BeautifulSoup) -> MIMEImage:
    """
    Function that finds address to main image of craiglist post, and formats the image
    
    @param soup: a Beautiful soup object of a craigslist post
    @returns: a MIMEImage object of a 200 x 200 image PNG
    """
    # get primary image URL from post 
    first_image=get_first(soup.findAll('img', {'title' : 1}))
    image_url=first_image['src']

    # get raw encoding of image, first comvert to PNG, then to MIMEImage
    r = requests.get(image_url, stream = True)
    if r.status_code == 200:
        img=Image.open(io.BytesIO(r.content))
        small=img.resize((200, 200))
        # convert to PNG encoding
        buf = io.BytesIO()
        small.save(buf, format='PNG')
        return(MIMEImage(buf.getvalue()))

def count_title_emoji(soup: bs4.BeautifulSoup) -> int:
    """
    Function that counts the number of emojis in the post title
    
    @param soup: BeauftifulSoup object created from a craigslist posting
    @returns: the number of emojis in the posting title
    """
    emojitext=get_first(soup.findAll('title'))
    return(sum([x in emoji.EMOJI_DATA for x in emojitext]))

def parse_posting_info(soup: bs4.BeautifulSoup) -> tuple:
    """
    Function that extracts out post ID and posting time
    
    @param soup: BeauftifulSoup object created from a craigslist posting
    @returns: a tuple with posting ID, and posting date
    """
    post_info=soup.findAll('p', {'class' : 'postinginfo'})
    post_id, posted=(None, None)
    for i in post_info:
        text=i.text
        post_id
        if 'post id' in text:
            post_id=text.split(":")[1].strip()
        elif 'posted' in text:
            posted=text.split(":")[1].strip().split(" ")[0]                   
    return(post_id, posted)

def get_coords(soup: bs4.BeautifulSoup)-> tuple:
    """
    Function that pulls latitude and longitude coordinates from post
    
    @params soup: BeautifulSoup object created from a craigslist posting
    @returns: a tuple of (latitude, longitude)
    """
    try: 
        map_info=soup.findAll('div', {'class' : 'viewposting'})[0]
        lat=map_info['data-latitude']
        long=map_info['data-longitude']
        return((lat,long))
    except:
        return((None, None))
    
def get_posting_text(soup: bs4.BeautifulSoup) -> tuple:
    """
    This function extracts the main post text and checks for web links (indicative of scams)
    
    @param soup: BeautifulSoup object created from a craigslist posting
    @returns: tuple containing a T/F indicator whether the listing text contains web links and the first 100 characters of the listing text
    """
    links=False
    body_soup=get_first(soup.findAll('section', {'id' : 'postingbody'}))
    if body_soup == None:
        print("no text in posting")
        raise ValueError
    body=body_soup.replace('QR Code Link to This Post' , '').replace('\n' , '')
    if re.findall(r'(http|www)[s]?', body):
        links=True
    snippet=body[0:100]
    return(links,snippet)

def dog_friendliness(soup: bs4.BeautifulSoup) -> str:
    """
    Function to look for pet friendliness indicators in post soup or post body text
    
    @param soup: BeautifulSoup object created from a craigslist posting
    @returns: an indicator of dog friendliness, can be: yes, no, or unknown
    """ 
    doggo='unknown'
    # first look for tag indicating dog friendly
    if sum(['dog' in x.text for x in soup.findAll('span')]) > 0:
        doggo='yes'
    # next search for 'no dogs' in text
    elif re.search(r'no (pet|dog|animal)s?', soup.text.lower()):
        doggo='no'
    return(doggo)

def get_scam(soup: bs4.BeautifulSoup, keywords: list) -> bool:
    """
    Function that searches listing soup object for scam keywords defined in parameters.py
    
    @param soup: BeautifulSoup object created from a craigslist posting
    @param keywords: a list of keywords to search for
    @returns: T/F indicator of whether any of the keywords are present
    """
    scam=bool(re.search(r'|'.join(keywords), soup.text.lower()))
    return(scam)

def metrics_from_soup(soup: bs4.BeautifulSoup, url: str, keywords: list, maps_key: str) -> list:
    """
    Main parsing function
    This function collects a number of metrics from the listing soup object
    
    lat, long - latitude and longitude
    posting id, posted - when post was created
    price
    images - number of images attached to posting
    emoji - number of emojis in post title
    scam - a T/F indicator for scam keywords
    dog - yes, no, unknown indicator of dog friendliness
    links - T/F indicator of web links in post text
    post_image - binary representation of main post image
    snippet - first 100 characters of the listing text
    address - a list with address, zipcode, neighborhood, and locality 

    @param soup: BeautifulSoup object created from a craigslist posting
    @param url: URL for craigslist post
    @param keywords: a list of keywords to search for
    @param maps_key: API ket to Google maps
    @returns: a dataframe of metrics 
    """
    price=get_first(soup.findAll('span', {'class' : 'price'}))
    images=len(soup.findAll("a", {"class":"thumb"}))
    emoji=count_title_emoji(soup)
    scam=get_scam(soup, keywords)
    posting_id, posted=parse_posting_info(soup)
    lat, long=get_coords(soup)
    dog=dog_friendliness(soup)
    links, snippet=get_posting_text(soup)
    post_image=get_and_resize_image(soup)
    address=reverse_lookup(maps_key, lat, long)
    postal_address, zipcode, neighborhood, locality=address
    print(postal_address)
    results_dict={posting_id : 
     {'url' : url,
      'price' : price,
      'num_images' : images,
      'dog' : dog,
      'scam' : scam,
      'links' : links,
      'emoji' : emoji,
      'locality' : locality,
      'date_posted' : posted,
      'latitude' : lat,
      'longitude' : long,
      'post_image' : post_image,
      'snippet' : snippet
    }}
    
    df=pd.DataFrame.from_dict(results_dict, columns=list(results_dict[posting_id].keys()), orient='index') 
    return(df)

import argparse
import logging

from ScamSifter.helpers import *
from ScamSifter.lib import *
from ScamSifter.maps import *
from ScamSifter.email import *
from ScamSifter.parameters import SEARCH_STEMS
from ScamSifter.parameters import SCAM_KEYWORDS

def main():
    # parse command line
    parser=argparse.ArgumentParser(description='ScamSifter: a command line tool that searches craigslist and filters out scam postings')
    parser.add_argument('base_path', type=str, nargs=1, help='base output path for files')
    parser.add_argument('api', type=str, nargs=1, help='path to file with Google maps API key')
    parser.add_argument('mailto', type=str, nargs=1, help='email address to send alters to')
    parser.add_argument('gmail_creds', type=str, nargs=1, help='path to Gmail token json file')
    arguments=parser.parse_args()
    base_path=arguments.base_path[0]
    api=arguments.api[0]
    mailto=arguments.mailto[0]
    gmail_creds=arguments.gmail_creds[0]

    # set api key as global variable
    with open(api, 'r') as file:
        maps_key=file.read().rstrip()

    # import craigslist search stem URLs from parameters.py
    searches=list(SEARCH_STEMS.values())    

    # first check if requires directories are present, if not, create
    log_path, database_path=create_paths(base_path)

    # set up logging
    curr_time=datetime.datetime.today().strftime("%d%m%Y_%H:%M")
    logging.basicConfig(filename=os.path.join(log_path, curr_time + '.log.txt'), format='%(message)s    %(asctime)s',
                   level=logging.INFO, filemode='w')

    # check for database file, if not present, create empty database list
    database_file=os.path.join(database_path, 'listing.database.txt')
    if not os.path.exists(database_file):
        database=[]
    else:
        database=pd.read_csv(database_file, header=None)[0].values

    logging.info('Database currently contains %s listings' % (len(database)))

    # get urls from all posts that match our critera, then subset to those that aren't in our database
    recent_urls=[search_links(stem, database) for stem in searches]
    flat_urls=[item for sublist in recent_urls for item in sublist]    

    logging.info("scraping %s links" % (len(set(flat_urls))))

    # scrape data for these urls 
    CL_dict=scrape_data(flat_urls)

    # parse soup
    outlist=[]
    fails=0
    for key, value in CL_dict.items():
        try:
            print(metrics_from_soup(value, key, SCAM_KEYWORDS, maps_key))
            outlist.append(metrics_from_soup(value, key, SCAM_KEYWORDS, maps_key))
        except:
            logging.info("Listing ID %s failed" % (key))
            fails+=1

    # make dataframe
    out=pd.concat(outlist).reset_index()

    # filter spam and send email alert
    clean=filter_spam(out)

    print("%s non-spam postings" % (len(clean))) 

    compose_email(clean, mailto, maps_key, gmail_creds)
    try:
        FIN=pd.concat([pd.Series(database), out['index']])
        FIN.to_csv(database_file)
    except:
        logging.info("failure to update database file")
    logging.info("%s listings added to database, %s listings failed" % (len(out), fails))
    return()

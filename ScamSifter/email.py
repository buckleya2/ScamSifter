import base64
import email 
import io

from ScamSifter.helpers import *
from ScamSifter.maps import *
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from PIL import Image

def make_post_text(values: pd.DataFrame) -> str:
    """
    Function that takes in a row from the CL database and creates an email alert HTML text string
    
    @param values: row from a pd.DataFrame
    @returns: HTML text
    
    """
    postid, price, location, snippet, link, lat, long, date_posted, dog=values[['index','price','locality','snippet','url','latitude','longitude', 'date_posted', 'dog']]
    body='<tr><td><b>price:</b></td><td>%s</td></tr><tr><td><b>location:</b></td><td>%s</td></tr>\
    <tr><td><b>date posted:</b></td><td>%s</td></tr><tr><td><b>dog friendly:</b></td><td>%s</td>\
    <tr><td><b>snippet:</b></td><td>%s...</td></tr>\
    <tr><td><b>link:</b></td><td>%s</td></tr>' % (price, location, date_posted, dog, snippet, link)
    return(body)

def make_email_dict(df: pd.DataFrame, maps_key: str) -> dict:
    """
    A function that assembles a dict describing the content of the alert email. The dict has one record per
    listing. The key is the text desired for the email notification. The value is a list of images to attach.
    Email alert should have 2 images, a Google map showing the location and one thumbnail from the post
    
    @param df: scam filtered pd.Dataframe with listing information
    @param maps_key: API key to Google maps
    @returns: email_dict, a dictionary with email HTML encoded test as key, images to attach as values
    """
    email_dict={}
    for row in df.iterrows():
        postid=row[0]
        values=row[1]
        url=values['url']
        lat=values['latitude']
        long=values['longitude']
        post_image=values['post_image']
        body=make_post_text(values)
        img1=get_map(lat, long, maps_key)
        email_dict[body] = [img1, post_image]
    return(email_dict)

def make_html(email_dict: dict) -> MIMEText:
    """
    Function that makes html text portion of message, including placeholders for inline images
    
    @param email_dict: output of make_email_dict, a dict with the email body text as a key, the images to attach as values
    @returns: HTML encoded email text
    """
    start=1
    outlist=[]
    for body, image_list in email_dict.items():
        num_images=len(image_list)
        html='<table>' + body + '<tr><td colspan="2">'
        image_string=''.join(['<img align="center" width="50%" height="50%" src="cid:image' \
                              + str(i) + '">' for i in range(start, num_images+start)])
        outlist.append(html + image_string + '</td></tr></table>')
        start=start + num_images
    msgText=MIMEText(''.join(['<html><body>'] + outlist + ['</body></html>']), 'html')
    return(msgText)

def add_images(message: MIMEText, email_dict: dict) -> MIMEText:
    """
    Function that attaches inline images to an email message
    
    @param message: a MIMEMultipart object to attach images to
    @param email_dict: output of make_email_dict, a dict with the email body text as a key, the images to attach as values
    @returns: a MIMEMultipart email message with images added for inline viewing
    """
    # start a running sum of all images attached to ensure proper header naming
    start=1
    # for each image, add header and attach to message
    for body, image_list in email_dict.items():
        for msgImage in image_list:
            msgImage.add_header('Content-ID', '<image' + str(start) + '>')
            msgImage.add_header('Content-Disposition', 'inline')
            message.attach(msgImage)
            start=start+1
    return(message)

def create_email(sender: str, to: str, subject: str, email_dict: dict):
    """
    Function that assembles a MIMEMultipart email message with inline images
    
    @param sender: sender of email, needs to have gmail API set up
    @param to: recipient 
    @param subject: title of email
    @param email_dict: output of make_email_dict, a dict with the email body text as a key, the images to attach as values
    @returns: base64 encoding of the email message in a dict format for Gmail API
    """
    # initiate message
    message = MIMEMultipart('related')
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = to
    
    # create alternative part for inline images
    msgAlternative = MIMEMultipart('alternative')
    message.attach(msgAlternative)
    
    # create the html text portion of the email and attach
    msgText=make_html(email_dict)
    msgAlternative.attach(msgText)
 
    # attach inline images to email
    message=add_images(message, email_dict)
    return({'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()})

def send_message(creds: str, message: dict) -> str:
    """
    Function that sends message via Gmail API
    
    @param cred: Gmail API credentials json filepath
    @param message: output of create_email, a dict containing base64 encoded MIME message
    @returns: message id
    """
    cred = Credentials.from_authorized_user_file(creds)
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']                                         
    service = build('gmail', 'v1', credentials=cred)
    message = (service.users().messages().send(userId='me', body=message).execute())
    return('Message Id: %s' % message['id'])

def compose_email(df: pd.DataFrame, mailto: str, maps_key: str, gmail_creds: str) -> str:
    """
    Function that generates HTML encoded email alert for new postings
    
    @param df: scam filtered pd.Dataframe with listing information
    @param mailto: address to send email alter to
    @param maps_key: API ket to Google maps
    @param gmail_creds: path to Gmail API credentials JSON file
    @returns: message ID
    """
    email_dict=make_email_dict(df, maps_key)
    alerts=list(email_dict.keys())
    # for every 20 listings, generate one email alert
    ids=[]
    for i in range(0,len(alerts),20):
        subset={x: email_dict[x] for x in alerts[i:i+20]}
        message=create_email('me', mailto, 'Housing Email Alert', subset)
        ids.append(send_message(gmail_creds, message))
    return(' '.join(ids))

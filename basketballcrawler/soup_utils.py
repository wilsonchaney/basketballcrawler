import logging
import requests
from bs4 import BeautifulSoup

def get_soup_from_url(url):
    """
    This function grabs the url and returns and returns the BeautifulSoup object
    """

    logging.debug("Getting soup from %s" % url)

    try:
        r = requests.get(url)
    except:
        return None

    return BeautifulSoup(r.text, "html5lib")


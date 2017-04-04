import requests
from bs4 import BeautifulSoup

def get_soup_from_url(url, suppress_output=True):
    """
    This function grabs the url and returns and returns the BeautifulSoup object
    """
    if not suppress_output:
        print url

    try:
        r = requests.get(url)
    except:
        return None

    return BeautifulSoup(r.text, "html5lib")


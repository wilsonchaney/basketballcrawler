import json
import logging
import string
import time
from difflib import SequenceMatcher

import pandas as pd

from player import Player, get_soup_from_url

BASKETBALL_LOG = 'basketball.log'

logging.basicConfig(filename=BASKETBALL_LOG,
                    level=logging.DEBUG,
                    )


def get_player_names_and_URLs():
    names = []

    for letter in string.ascii_lowercase:
        letter_page = get_soup_from_url('http://www.basketball-reference.com/players/%s/' % (letter))

        # we know that all the currently active players have <strong> tags, so we'll limit our names to those
        current_names = letter_page.findAll('strong')
        for n in current_names:
            name_data = n.children.next()
            try:
                names.append((name_data.contents[0], 'http://www.basketball-reference.com' + name_data.attrs['href']))
            except Exception as e:
                pass
        time.sleep(1)  # sleeping to be kind for requests

    return dict(names)


def build_player_dictionary():
    """
    Builds a dictionary for all current players in the league-- this takes about 10 minutes to run!
    """

    logging.debug("Begin grabbing name list")
    player_names_and_urls = get_player_names_and_URLs()
    logging.debug("Name list grabbing complete")

    players = {}
    for name, url in player_names_and_urls.items():
        players[name] = Player(name, url, scrape_data=True)
        time.sleep(1)  # sleep to be kind.

    logging.debug("buildPlayerDictionary complete")

    return players


def fuzzy_ratio(name, search_string):
    """
    Calculate difflib fuzzy ratio
    """
    return SequenceMatcher(None, search_string.lower(), name.lower()).ratio()


def search_for_name(player_dictionary, search_string, threshold=0.5):
    """
    Case insensitive partial search for player names, returns a list of strings,
    names that contained the search string.  Uses difflib for fuzzy matching.
    threshold:
    """
    players_name = player_dictionary.keys()
    search_string = search_string.lower()
    players_ratio = map(lambda name: [name, fuzzy_ratio(name, search_string)], players_name)
    searched_player_dict = [name for name in players_name if search_string in name.lower()]
    searched_player_fuzzy = [player for (player, ratio) in players_ratio if ratio > threshold]
    return list(set(searched_player_dict + searched_player_fuzzy))


def save_player_dictionary(player_dictionary, path_to_file):
    """
    Saves player dictionary to a JSON file
    """
    player_json = {name: player_data.to_json() for name, player_data in player_dictionary.items()}
    json.dump(player_json, open(path_to_file, 'wb'), indent=0)


def load_player_dictionary(pathToFile):
    """
    Loads previously saved player dictionary from a JSON file
    """
    result = {}
    with open(pathToFile) as f:
        json_dict = json.loads(f.read())
        for player_name in json_dict:
            parsed_player = Player(None, None, False)
            parsed_player.__dict__ = json_dict[player_name]
            result[player_name] = parsed_player
    return result


def df_from_gamelog_url_list(gamelogs):
    """
    Functions to parse the gamelogs
    Takes a list of game log urls and returns a concatenated DataFrame
    """
    return pd.concat([df_from_gamelog_url(g) for g in gamelogs])


def df_from_gamelog_url(url):
    """
    Takes a url of a player's game log for a given year, returns a DataFrame
    """
    glsoup = get_soup_from_url(url)

    reg_season_table = glsoup.findAll('table', attrs={'id': 'pgl_basic'})  # id for reg season table
    playoff_table = glsoup.findAll('table', attrs={'id': 'pgl_basic_playoffs'})  # id for playoff table

    # parse the table header.  we'll use this for the creation of the DataFrame
    header = []
    for th in reg_season_table[0].findAll('th'):
        if not th.getText() in header:
            header.append(th.getText())

    # add in headers for home/away and w/l columns. a must to get the DataFrame to parse correctly

    header[5] = u'HomeAway'
    header.insert(7, u'WinLoss')

    reg = soup_table_to_df(reg_season_table, header)
    playoff = soup_table_to_df(playoff_table, header)

    if reg is None:
        return playoff
    elif playoff is None:
        return reg
    else:
        return pd.concat([reg, playoff])


def soup_table_to_df(table_soup, header):
    """
    Parses the HTML/Soup table for the gamelog stats.
    Returns a pandas DataFrame
    """
    if not table_soup:
        return None
    else:
        rows = table_soup[0].findAll('tr')[1:]  # all rows but the header

        # remove blank rows
        rows = [r for r in rows if len(r.findAll('td')) > 0]

        parsed_table = [[col.getText() for col in row.findAll('td')] for row in rows]  # build 2d list of table values
        return pd.io.parsers.TextParser(parsed_table, names=header, index_col=2, parse_dates=True).get_chunk()


def game_logs(playerDictionary, name):
    ### would be nice to put some caching logic here...
    return df_from_gamelog_url_list(playerDictionary[name].gamelog_url_list)

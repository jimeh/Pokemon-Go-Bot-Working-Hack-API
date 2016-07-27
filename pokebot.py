# Credits to Tejado and the devs over at the subreddit /r/PokemonGoDev -TomTheBotter

# Do NOT use this bot while signed into your phone -TomTheBotter

# If you want to make the bot as fast as possible for catching more pokemon (like you are driving a fast car--it won't
# look suspicious though, since it only goes on paths), make stepsize 200.
# For more info see that method in pgoapi.py under pgoapi... but still I wouldn't recommend making stepsize that high.
from multiprocessing import Process

import flask
import os
import json
import thread
import logging
import argparse

from flask.helpers import send_from_directory
from flask.templating import render_template
from pgoapi import PGoApi
from geopy.geocoders import GoogleV3
from flask import Flask

log = logging.getLogger(__name__)

app = Flask(__name__)
api = None


class MyServer:
    def __init__(self):
        self.globalData = "hello"

app = Flask(__name__)
my_server = MyServer()


@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')


@app.route('/api/player')
def api_player():
    res = my_server.api.get_player().call()
    data = res['responses']['GET_PLAYER']['player_data']
    return flask.jsonify(data)


@app.route('/api/inventory')
def api_inventory():
    res = my_server.api.get_inventory().call()
    data = res['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
    return flask.jsonify(data)


@app.route('/api/pokemon_names')
def api_pokemon_names():
    print(my_server.api)
    return flask.jsonify(my_server.api.pokemon_names)


def start_server():
    app.run(host="0.0.0.0", port=3000, debug=False, use_reloader=False, threaded=True)


def get_pos_by_name(location_name):
    geolocator = GoogleV3()
    loc = geolocator.geocode(location_name)
    log.info('Your given location: %s', loc.address.encode('utf-8'))
    log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)
    return loc.latitude, loc.longitude, loc.altitude

    # If you are having problems with the above three lines;
    # That means your API isn't configured or it expired or something happened related to api.
    # If that is the case, just manually input the coordinates of you current location.
    # Don't make it something too ridiculous, or it might result in a soft ban.
    # For example, you would replace the above three lines with something like: return (33.0, 112.0, 0.0)


def init_config():
    parser = argparse.ArgumentParser()
    config_file = "config.json"
    load = {}
    if os.path.isfile(config_file):
        with open(config_file) as data:
            load.update(json.load(data))

    required = lambda x: not x in load['accounts'][0].keys()
    parser.add_argument("-a", "--auth_service", help="Auth Service ('ptc' or 'google')",
                        required=required("auth_service"))
    parser.add_argument("-i", "--config_index", help="config_index", required=required("config_index"))
    parser.add_argument("-u", "--username", help="Username", required=required("username"))
    parser.add_argument("-p", "--password", help="Password", required=required("password"))
    parser.add_argument("-l", "--location", help="Location", required=required("location"))
    parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    parser.add_argument("-c", "--cached", help="cached", action='store_true')
    parser.add_argument("-t", "--test", help="Only parse the specified location", action='store_true')
    parser.set_defaults(DEBUG=False, TEST=False, CACHED=False)
    config = parser.parse_args()
    load = load['accounts'][int(config.__dict__['config_index'])]
    config.__dict__.update(load)
    if config.auth_service not in ['ptc', 'google']:
        log.error("Invalid Auth service specified! ('ptc' or 'google')")
        return None

    return config


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pgoapi").setLevel(logging.INFO)
    logging.getLogger("rpc_api").setLevel(logging.INFO)

    config = init_config()
    if not config:
        return

    if config.debug:
        logging.getLogger("requests").setLevel(logging.INFO)
        logging.getLogger("pgoapi").setLevel(logging.DEBUG)
        logging.getLogger("rpc_api").setLevel(logging.INFO)

    position = get_pos_by_name(config.location)
    if config.test:
        return

    pokemon_names = json.load(open("name_id.json"))
    api = PGoApi(config.__dict__, pokemon_names)

    api.set_position(*position)
    my_server.api = api

    if not api.login(config.auth_service, config.username, config.password, config.cached):
        return
    while True:
        # try:
        api.main_loop()
        # except Exception as e:
        #     log.error('Main loop has an ERROR, restarting %s', e)
        #     sleep(30)
        #     main()


if __name__ == '__main__':
    # p = Process(target=start_server)
    # p.daemon = True
    # p.start()
    thread.start_new_thread(start_server,())
    main()
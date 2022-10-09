import json
import threading
import time
import requests
from datetime import date, datetime
import pickle
from pathlib import Path
import sys
import os
import argparse
import logging

import webpage
from aircraft import Aircraft


# parse command line arguments
parser = argparse.ArgumentParser('Planes over Western suburbs')
parser.add_argument('--noweb', '-n', 
    dest='web', action='store_const',
    const=False, default='True',
    help='dont push pages to webserver')
parser.add_argument('--progress', '-p',
    dest='progress', action='store_const',
    const=True, default=False,
    help='display # during every sleep')
parser.add_argument('--verbose', '-v',
    dest='verbose', action='store_const',
    const=True, default=False,
    help='send log output to stdout')
args = parser.parse_args()

# setup logging
if args.verbose:
    logfilename = None
else:
    logfilename = 'planes.log'
logging.basicConfig(
    filename=logfilename, 
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO,
    )

logging.info('********************************* STARTUP')

# curl "https://petercorke:opensky123@opensky-network.org/api/states/all?lamin=-27.53534&lamax=-27.44830&lomin=152.89735&lomax=153.03248"

# s = '{"time":1661577066,"states":[["7c6d8d","QFA758  ","Australia",1661577065,1661577065,152.9833,-27.487,2385.06,false,141.74,284.29,18.86,null,2537.46,null,false,0],["88510b","THA492  ","Thailand",1661577065,1661577065,153.0113,-27.4659,11582.4,false,199.15,300.08,0,null,12016.74,"0245",false,0]]}'

test_data = '{"time":1661570048,"states":[["7c16e1","RSCU500 ","Australia",1661570048,1661570048,152.9835,-27.5056,205.74,false,74.38,328.29,-0.65,null,358.14,"6066",false,0],["7c7a36","VOZ1117 ","Australia",1661570048,1661570048,153.0017,-27.4903,2057.4,false,136.16,279.57,16.91,null,2217.42,"4434",false,0]]}'
test_data = None

pickle_file = Path("planes.pickle")
if not pickle_file.exists():
    pickle_file = Path("~/planes.pickle").expanduser()


if __name__ == "__main__":

    credentials = os.getenv('OPENSKY')
    if credentials is None:
        logging.error('setup envariable OPENSKY as username:password')
        sys.exit(1)

    pause = 90

    # build the URL
    latitude = (-27.53534, -27.44830)
    longitude = (152.89735, 153.03248)
    url = f"https://{credentials}@opensky-network.org/api/states/all?lamin={latitude[0]}&lamax={latitude[1]}&lomin={longitude[0]}&lomax={longitude[1]}"

    # attempt to load checkpointed state from the pickle file
    try:
        with open(pickle_file, "rb") as fp:
            data = pickle.load(fp)
            planes_today = data[0]
            last10 = data[1]
            perday = data[2]
            today = data[3]
            if len(data) > 4:
                allplanes = data[4]
            else:
                allplanes = planes_today.copy()
        logging.info("loaded state from " + str(pickle_file))
    except:
        # no state file
        planes_today = []
        last10 = []
        perday = []
        today = date.today()
        allplanes = []
        logging.info("initialize state")

    # planes_today: a list of Aircraft instances
    # perday: a list of tuples (number, date)
    # today: date instance, current date

    webpage.generate(planes_today, last10, perday, allplanes, 100)

    once = False
    nfail = 0

    while True:

        # periodically update the webpage if server has been down for a while
        if nfail > 0 and nfail % 20 == 0:
            # a lot of failures, update the web page
            webpage.generate(planes_today, last10, perday, allplanes, nfail)
            if args.web:
                webpage.upload()

        # sleep for a bit, to reduce the number of Open-Sky requests
        if once:
            time.sleep(pause)  # pause on subsequent loops
            if args.progress:
                print('#', end='', file=sys.stdout)
                sys.stdout.flush()

        # deal with a new day, reset some variables, record daily stats
        if date.today() > today:
            logging.info('********************************* new day')

            total_for_the_day = len(planes_today)
            planes_today = [] # empty the list of planes
            perday.insert(0, (total_for_the_day, today, nfail))

            nfail = 0

            today = date.today()
            changes = True
            webpage.generate(planes_today, last10, perday, allplanes)
            if args.web:
                webpage.upload()

                try:
                    exit = os.system('scp -q planes.log sg:/home/u41-iqh6n5pf7kxl/www/petercorke.com/www')
                    if exit != 0:
                        logging.error(f'logfile upload failed, scp error {exit}')
                except:
                    logging.error('logfile upload failed, system failed')


        # attempt to get the state vector from OpenSky
        try:
            response = requests.get(url, timeout=5)
        #except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        except BaseException as err:
            logging.warning(f"requests.get failed: {err=}, {type(err)=}")
            nfail += 1
            continue

        # check request quota, print number remaining on first loop
        if response.status_code == 429:
            retry = int(response.headers['X-Rate-Limit-Retry-After-Seconds']) / 3600.0
            logging.warning(f"too many requests to OpenSky, retry after {retry:.2f} hours")
            continue
        else:
            if not once:
                try:
                    logging.info(f"OpenSky requests remaining: {response.headers['X-Rate-Limit-Remaining']}")
                except:
                    logging.warning('cant read header')
            json_text = response.text
        once = True

        # attempt to decode the state vector
        try:
            jsondata = json.loads(json_text)
        except json.JSONDecodeError:
            logging.warning('JSON decode fail ' + "|".join(json_text.split()))
            nfail += 1
            continue

        try:
            states = jsondata['states']
        except KeyError:
            # some request error
            logging.warning('JSON data has no state ' + json_text)
            nfail += 1
            continue

        if states is None:
            nfail += 1
            continue

        # we have a valid state vector, process the reported aircraft
        changes = False
        for state in states:
            plane = Aircraft(state)

            if plane.on_ground:
                # probs a helicopter
                # alt < 500m
                logging.info(' x on ground')
                continue

            logging.info(plane)

            if plane.airline == "":
                # not a known airline
                logging.info(' x unknown airline')
                continue

            try:
                if plane.baro_altitude is not None and plane.baro_altitude > 5000:
                    # flying over, not on approach or departure to BNE
                    logging.info(' x too low')
                    continue

                if plane.vertical_rate < 4:
                    # not climbing
                    logging.info(' x not climbing')
                    continue

                if plane.true_track < 180:
                    # heading east, landing from the south
                    logging.info(' x going east')
                    continue

                if plane.callsign in [p.callsign for p in planes_today[:5]]:
                    # seen recently
                    logging.info(' x seen previously')
                    continue

                planes_today.insert(0, plane)
                last10.insert(0, plane)
                last10 = last10[:10]
                allplanes.insert(0, plane)
                logging.info(' + candidate')
                changes = True

            except TypeError:
                logging.info('** failure in decision tree')
                continue

        # save the state
        with open(pickle_file, "wb") as fp:
            pickle.dump([planes_today, last10, perday, today, allplanes], fp)

        if changes and args.web:
            webpage.generate(planes_today, last10, perday, allplanes, nfail)
            webpage.upload()

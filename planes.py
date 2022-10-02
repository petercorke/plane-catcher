import json
import threading
import time
import requests
from datetime import date, datetime
import pickle
from pathlib import Path
import sys
import os
import webpage
from aircraft import Aircraft

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
        print('setup envariable OPENSKY as username:password')
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
        print("loaded state from ", str(pickle_file))
    except:
        # no state file
        planes_today = []
        last10 = []
        perday = []
        today = date.today()
        allplanes = []
        print("initialize state")

    # planes_today: a list of Aircraft instances
    # perday: a list of tuples (number, date)
    # today: date instance, current date

    webpage.generate(planes_today, last10, perday, allplanes)

    once = False
    while True:
        if once:
            time.sleep(pause)  # pause on subsequent loops
            print('#', end='', file=sys.stdout)
            sys.stdout.flush()

        if date.today() > today:
            # a new day, roll the data logs
            print('******** new day *********')

            total_for_the_day = len(planes_today)
            planes_today = [] # empty the list of planes
            perday.insert(0, (total_for_the_day, today))

            today = date.today()
            changes = True
            webpage.generate(planes_today, last10, perday, allplanes)
            webpage.upload()


        # get the state vector from OpenSky, check request quota
        if test_data is None:
            try:
                response = requests.get(url)
            except requests.exceptions.ConnectionError, except requests.exceptions.Timeout::
                print('connection/timeout error')
                continue
            if response.status_code == 429:
                retry = int(response.headers['X-Rate-Limit-Retry-After-Seconds']) / 3600.0
                print(f"too many requests to OpenSky, retry after {retry:.2f} hours")
                continue
            else:
                if not once:
                    try:
                        print(f"OpenSky requests remaining: {response.headers['X-Rate-Limit-Remaining']}")
                    except:
                        print('cant read header')
                json_text = response.text
        else:
            json_text = test_data

        once = True

        # attempt to decode the state vector
        try:
            jsondata = json.loads(json_text)
        except json.JSONDecodeError:
            print('JSON decode fail', json_text)
            continue

        try:
            states = jsondata['states']
        except KeyError:
            # some request error
            print('JSON no state data', json_text)
            continue

        if states is None:
            continue

        changes = False
        for state in states:
            plane = Aircraft(state)

            if plane.on_ground:
                # probs a helicopter
                # alt < 500m
                print(' x on ground')
                continue

            print('\n', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ":: ", plane)

            if plane.airline == "":
                # not a known airline
                print(' x unknown airline')
                continue

            try:
                if plane.baro_altitude is not None and plane.baro_altitude > 5000:
                    # flying over, not on approach or departure to BNE
                    print(' x too low')
                    continue

                if plane.vertical_rate < 4:
                    # not climbing
                    print(' x not climbing')
                    continue

                if plane.true_track < 180:
                    # heading east, landing from the south
                    print(' x going east')
                    continue

                if plane.callsign in [p.callsign for p in planes_today[:5]]:
                    # seen recently
                    print(' x seen previously')
                    continue

                planes_today.insert(0, plane)
                last10.insert(0, plane)
                last10 = last10[:10]
                allplanes.insert(0, plane)
                print(' + candidate')
                changes = True

            except TypeError:
                print('** failure in decision tree')
                continue

        # save the state
        with open(pickle_file, "wb") as fp:
            pickle.dump([planes_today, last10, perday, today, allplanes], fp)

        if changes:
            webpage.generate(planes_today, last10, perday, allplanes)
            webpage.upload()


    # day = date.fromtimestamp(plane.time)
    # if day > today:
    #     roll_the_day()
    #     today = day
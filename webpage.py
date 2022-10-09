from datetime import datetime
import os
import logging

css = r'''
    <style>

    * {
        font-family: Tahoma;
    }

    * {
        box-sizing: border-box;
    }

    /* Create two equal columns that floats next to each other */
    .column {
        float: left;
        width: 350px;
        padding: 10px;
        height: 300px; /* Should be removed. Only for demonstration */
    }

    /* Clear floats after the columns */
    .row:after {
        content: "";
        display: table;
        clear: both;
    }

    /* Responsive layout - makes the two columns stack on top of each other instead of next to each other */
    @media screen and (max-width: 600px) {
        .column {
            width: 100%;
        }
    }

    table, th, td {
        table-layout: fixed;
        border-collapse: collapse;
        border: 3px solid purple;
        padding-left: 20px;
        padding-right: 20px;
    }

    table {
        margin-left: 50px;
    }

    .table tbody tr.table-indent{
        padding-left:50px;
    }
    </style>
'''



def am_pm(i):
    if i < 12:
        return str(i) + "am"
    elif i == 12:
        return str(i) + "pm"
    elif i < 24:
        return str(i - 12) + "pm"
    else:
        return str(i - 12) + "am"

def generate(planes_today, last10, perday, allplanes, nfail):

    # ---------------------------- by the hour
    by_the_hour = r'''<table>
  <tr>
    <th>Time interval</th>
    <th>Number of planes</th> 
  </tr>
'''
    histo = [0,] * 24
    for plane in planes_today:
        histo[plane.time.hour] += 1
    for i, h in enumerate(histo):
        if h > 0:
            by_the_hour += f'''
    <tr>
      <td>{am_pm(i)}-{am_pm(i+1)}</td>
      <td>{h}</td>
'''
    by_the_hour += r'''
  </table>'''

    # ---------------------------- most recent
    most_recent = r'''<table>
  <tr>
    <th>Flight number</th>
    <th>Time heard</th> 
  </tr>
'''
    # for plane in sorted(planes_today, key=lambda x: x.ts, reverse=True)[:10]:
    for plane in last10:
        most_recent += f'''
    <tr>
      <td><a href="https://www.airportia.com/flights/{plane.flightNumber}">{plane.flightNumber}</a></td>
      <td>{plane.time.strftime("%I:%M%p %-d %b")}</td>
'''
    most_recent += r'''
  </table>'''

    # ---------------------------- last 7 days
    last7 = r'''<table>
  <tr>
    <th>Number of planes</th> 
    <th>Date</th>
    <th>Server downtime</th>
  </tr>
'''
    for data in perday[:7]:
        number = data[0]
        date = data[1]
        if len(data) == 3:
            failmins = f'{data[2]*1.5:.0f} mins'
        else:
            failmins = 'n/a'
        # third element nfail recently added
        last7 += f'''
    <tr>
      <td>{number}</td>
      <td>{date.strftime("%A (%-d %b)")}</td>
      <td>{failmins}</td>
'''
    last7 += r'''
  </table>'''

    # ---------------------------- night planes
    
    # table of planes taking off at night (10pm-6am)
    nightplanes = r'''<table>
  <tr>
    <th>Flight number</th>
    <th>Time heard</th> 
  </tr>
'''
    # for plane in sorted(planes_today, key=lambda x: x.ts, reverse=True)[:10]:
    for plane in allplanes:
        if plane.time.hour >= 22 or plane.time.hour < 6:
            nightplanes += f'''
    <tr>
      <td><a href="https://www.airportia.com/flights/{plane.flightNumber}">{plane.flightNumber}</a></td>
      <td>{plane.time.strftime("%I:%M%p %-d %b")}</td>
'''
    nightplanes += r'''
  </table>'''

    # server down
    if nfail > 2:
        server_down = f'''
        <p style="color:red;">Some aircraft today may not have been recorded. The Open-Sky network server which 
        provides our data has been down for {nfail*1.5:.0f} minutes so far today</p>
        '''
    else:
        server_down = ''

    # ---------------------------- create page
    fp = open('planes.html', 'w')

    template = f'''<html>
    <head>
        <!--prevent caching -->
        <meta http-equiv="Cache-Control" content="max-age=0, no-cache, no-store, must-revalidate" />
        <meta http-equiv="Pragma" content="no-cache" />
        <meta http-equiv="Expires" content="0" />
        <!-- responsive style -->
        <meta name="viewport" content="width=device-width, initial-scale=1">
        {css}
    </head>
    <body>
    <title>Planes over Brisbane's Western Suburbs</title>

    <h1>Planes over Brisbane's Western Suburbs</h1>
    <p>    Northbound aircraft taking off to the south from Brisbane airport turn right and fly along
    a track over the University of Queensland, Toowong and Mount Coot-tha.</p>

    <h2>So far today</h2>
    <p>{len(planes_today)} aircraft have taken off from Brisbane airport and flown low and loud over the Western suburbs.</p>

    {server_down}

    <h3>By the hour</h3>
    {by_the_hour}

    <h3>Last ten planes</h3>
    {most_recent}

    <h2>Last 7 days</h2>
    {last7}

    <h2>Why we need a curfew</h2>
    {nightplanes}

    <h2>Wind direction</h2>
    <div class="row">
        <div class="column">
            <a href="https://www.windfinder.com?utm_source=reportgraph&utm_medium=web&utm_campaign=homepageweather&utm_content=mediumgraph"><img src="https://www.windfinder.com/wind-cgi/windgraph_medium.pl?STATIONSNR=au21&UNIT_WIND=kts&UNIT_TEMPERATURE=c" border="0" /></a><noscript><a rel="nofollow" href="https://www.windfinder.com/report/brisbane_airport?utm_source=report&utm_medium=web&utm_campaign=homepageweather&utm_content=noscript-report">Wind forecast for Brisbane Airport</a> provided by <a rel="nofollow" href="https://www.windfinder.com?utm_source=report&utm_medium=web&utm_campaign=homepageweather&utm_content=noscript-logo">windfinder.com</a></noscript>
        </div>
        <div class="column">
            <p>Whether aircraft on the new runway take off to the south (19R) and come over
            the Western suburbs, or go north (01L) over the bay depends on wind direction.
            Aircraft cannot take off with a tailwind greater than 5 knots (9.2 km/h).  If the wind
            at the airport has a strong southerly component then the planes cannot take off
            over the bay and they will come our way.</p>
        </div>
    </div>

    <h2>Other resources</h2>
    <ul>
    <li><a href="https://ehq-production-australia.s3.ap-southeast-2.amazonaws.com/9253dbc1f71d0e8b99406a455dcabae8c2d3c2ee/original/1642575383/2bf0c417f5b59c60cab6018fbf62492d_Brisbane_Runway_Operations.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAIBJCUKKD4ZO4WUUA%2F20220828%2Fap-southeast-2%2Fs3%2Faws4_request&X-Amz-Date=20220828T050333Z&X-Amz-Expires=300&X-Amz-SignedHeaders=host&X-Amz-Signature=18cd61c8bafd2d9b93b8117a8cc52d1367a814f08c7af00988d6c55ca6f0609c">Fact sheet: runway operations</a></li>
    <li><a href="https://www.airservicesaustralia.com/wp-content/uploads/BNE-NPR-PIR-Independent-Review_Final-Report-v1.0_final.pdf">Independent Review - final report</a></li>
    <li><a href="https://bfpca.org.au">Brisbane Flight Path Community Alliance</a> - people before planes</li>
    <li><a href="https://www.bne.com.au/corporate/community-and-environment/flight-paths-aircraft-noise/enquiries">To complain about aircraft noise</a></ul>

    <h2>How this site works</h2>

    <div class="row">
        <div class="column">
            <a href="map.png"><img src="map.png" width="300"></a>
        </div>
        <div class="column">
            <p>A server checks the <a href="http://www.opensky-network.org">OpenSky Network</a>
            every 90 seconds for all aircraft within the zone shown at the left.  Statistics are
            gathered for all aircraft flying at jet speed, below 2000m, climbing and heading west.
            </p>
        </div>
    </div>

    
    <h3>Privacy notices</h3>
    <ul>
    <li>This site does not use cookies.</li>
    <li>This site uses Google Analytics to monitor traffic.</li>
    <li>On this website the weather widget of Windfinder.com GmbH &amp; Co.KG is integrated. 
    Your IP address will be transmitted to Windfinder.com GmbH &amp; Co.KG to display the weather data. 
    Further personal data will not be transmitted. 
    Your IP address will be logged by Windfinder.com GmbH &amp; Co.KG for technical reasons and deleted after 7 days. </li>                 
    </ul>

    <p style="font-size:70%;">Page created at {datetime.now().isoformat()}</p>
    </body>
</html>
'''

    print(template, file=fp)
    fp.close()
    logging.debug("web page written")

def upload():
    try:
        exit = os.system('scp -q planes.html sg:/home/u41-iqh6n5pf7kxl/www/petercorke.com/www')
        if exit != 0:
            logging.error(f'webpage upload failed, scp error {exit}')
    except:
        logging.error('webpage upload failed, system failed')
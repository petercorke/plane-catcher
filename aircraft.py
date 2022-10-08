from datetime import date, datetime
import logging

airlines = {
    # ICAO  IATA  airline-name
    "QFA": ("QF", "Qantas"),
    "QLK": ("QF", "Qantas Link"),
    "QJE": ("QF", "Qantas Link"),
    "NWK": ("QF", "Qantas Link"),
    "JST": ("JQ", "Jetstar"),
    "RXA": ("ZL", "Rex Airlines"),
    "VOZ": ("VA", "Virgin Australia"),
    "UAE": ("EK", "Emirates"),
    "ANZ": ("NZ", "Air New Zealand"),
    "QTR": ("QR", "Qatar Airways"),
    "SIA": ("SQ", "Singapore Airlines"),
    "EVA": ("BR", "EVA Airways"),
    "FJI": ("FJ", "Fiji Airways"),
    "THA": ("TG", "Thai Airways International"),
    "UTY": ("QQ", "Alliance Airlines"),
    "ANO": ("TL", "Airnorth"),
    "SOL": ("IE", "Solomen Airlines"),
    "TGW": ("TR", "Scoot Tiger Air"),
    "THA": ("TG", "Thai Airways"),
    "CAL": ("CI", "China Airlines"),
    "ANG": ("PX", "Air Niugini"),
    "HAL": ("HA", "Hawaiian Airlines"),
    "PAL": ("PR", "Phillipine Airlines"),
    "ETD": ("EY", "Etihad Airlines"),
    "ACA": ("AC", "Air Canada"),
    "AVN": ("NF", "Air Vanuatu"),
    "CPA": ("CX", "Cathay Pacific Airlines"),
    "CES": ("MU", "China Eastern Airlines"),
    "CSN": ("CZ", "China Southern Airlines"),
    "RON": ("ON", "Naruu Airlines"),
    "MXD": ("OD", "Malindo Air"),
    "TRF": ("TOLL", "Toll Priority"),
    "TXF": ("TOLL", "Toll Priority"),
}

class Aircraft:
    def __init__(self, data):
        self.icao24 = data[0]
        self.callsign = data[1]
        self.origin_country = data[2]
        self.ts = data[3]
        self.last_contact = data[4]
        self.longitute = data[5]
        self.latitude = data[6]
        self.baro_altitude = data[7]
        self.on_ground = data[8]
        self.velocity = data[9]
        self.true_track = data[10]
        self.vertical_rate = data[11]
        self.sensors = data[12]
        self.geo_altitude = data[13]
        self.squawk = data[14]
        self.spi = data[15]
        self.position_source = data[16]
        self.flightNumber = ""
        self.airline = ""

        self.time = datetime.fromtimestamp(self.ts)

        try:
            self.helicopter = self.velocity < 100 and self.baro_altitude < 500
        except:
            self.helicopter = False
            logging.warning('failure in helicopter logic', self)

        try:
            airline = airlines[self.callsign[:3].upper()]
            self.flightNumber = airline[0] + self.callsign[3:].rstrip()
            self.airline = airline[1]
        except KeyError:
            self.flightNumber = self.callsign.lower()
            self.airline = ""
        

    def __str__(self):

        s = f"{self.time.strftime('%Y-%m-%d %H:%M:%S')}:  {self.flightNumber} ({self.airline}) heading={self.true_track} alt={self.baro_altitude}m climb={self.vertical_rate}m/s, speed={self.velocity}m/s, callsign={self.callsign}, icao={self.icao24}"
        if self.helicopter:
            s = "HELI " + s
        return s
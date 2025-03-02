import os
from datetime import datetime

import requests
from sortedcontainers import SortedSet

from model.line import Line
from model.station import Station
from network.network import Network

URL = 'https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring'
HEADERS = {'Accept': 'application/json', 'apikey': os.getenv('IDFM_API_KEY')}

NAME = "Île-de-France"
SCHEMA_NAME = "IDFM"


class IDFM(Network):
    def __init__(self):
        super().__init__(NAME, SCHEMA_NAME)

    def get_color(self, id_ligne: str) -> hex:
        return self._database.get_color(self.to_idfm(id_ligne))

    def get_stop_name(self, id_arret: str) -> str:
        return self._database.get_stop_name(self.to_idfm(id_arret))

    def get_line_name(self, ligne: str) -> str:
        return self._database.get_line_name(self.to_idfm(ligne))

    @staticmethod
    def to_stif(string: str) -> str:
        """Convertit au format STIF toute chaîne de caractères"""
        if 'STIF' in string:
            return string
        if 'C' in string:
            return f"STIF:Line::{string[5:]}:"
        return f"STIF:StopPoint:Q:{string[5:]}:"

    @staticmethod
    def to_idfm(string: str) -> str:
        """Convertit au format IDFM toute chaîne de caractères"""
        if 'IDFM' in string:
            return string
        if 'Line' in string:
            return f"IDFM:{string[11:-1]}"
        return f"IDFM:{string[17:-1]}"

    def create_station(self, station_id: str) -> Station:
        station: Station = Station(station_id, self.get_stop_name(station_id))

        station.lines = SortedSet(key=lambda ligne: ligne.id)
        params = {'MonitoringRef': self.to_stif(station.id)}

        try:
            json = requests.get(URL, headers=HEADERS, params=params).json()
            json = json['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']
        except Exception as e:
            print(e)
            raise

        for entry in json:
            stop_id: str = entry['MonitoringRef']['value']
            journey: dict = entry['MonitoredVehicleJourney']
            line_id: str = journey['LineRef']['value']
            line: Line = station.get_line(line_id)

            if not line:
                line = Line(line_id, self.get_line_name(line_id), self.get_color(line_id))
                station.add_line(line)

            line.add_stop(stop_id, self.get_stop_name(stop_id))

            wait_time = journey['MonitoredCall'].get('ExpectedDepartureTime', '2022-01-01T00:00:00.000Z')
            wait_time = journey['MonitoredCall'].get('ExpectedArrivalTime', wait_time)
            wait_time = datetime.strptime(wait_time, '%Y-%m-%dT%H:%M:%S.%fZ')
            wait_time = round((wait_time - datetime.now()).total_seconds() / 60.0)

            destination = journey['MonitoredCall'].get('DestinationDisplay')
            destination = journey.get('DestinationName', destination)
            destination = journey.get('DirectionName', destination)
            destination = destination[0]['value']

            if journey['JourneyNote'] and journey['JourneyNote'][0]['value'] != "":
                destination = f"{journey['JourneyNote'][0]['value']} | {destination}"

            if wait_time >= 0:
                line.get_stop(stop_id).add_timetable_record(destination, wait_time)

        return station
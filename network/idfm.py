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

        station.lignes = SortedSet(key=lambda ligne: ligne.id)
        params = {'MonitoringRef': self.to_stif(station.id)}

        try:
            json = requests.get(URL, headers=HEADERS, params=params).json()
        except Exception as e:
            print(e)
            raise

        json = json['Siri']['ServiceDelivery']['StopMonitoringDelivery'][0]['MonitoredStopVisit']

        for entree in json:
            id_arret = entree['MonitoringRef']['value']
            id_ligne = str(entree['MonitoredVehicleJourney']['LineRef']['value'])

            line: Line = Line(id_ligne, self.get_line_name(id_ligne), self.get_color(id_ligne))
            line = station.get_line() if station.get_line(id_ligne) else station.add_line(line)

            line.add_stop(id_arret, self.get_stop_name(id_arret))

            attente_depart = entree['MonitoredVehicleJourney']['MonitoredCall'].get(
                    'ExpectedDepartureTime', '2022-01-01T00:00:00.000Z')
            attente_arrivee = entree['MonitoredVehicleJourney']['MonitoredCall'].get(
                    'ExpectedArrivalTime', attente_depart)
            attente = datetime.strptime(attente_arrivee, '%Y-%m-%dT%H:%M:%S.%fZ')
            attente = round((attente - datetime.now()).total_seconds() / 60.0)

            destination = entree['MonitoredVehicleJourney']['MonitoredCall'].get('DestinationDisplay')
            destination = entree['MonitoredVehicleJourney'].get('DestinationName', destination)
            destination = destination[0]['value']

            if entree['MonitoredVehicleJourney']['JourneyNote'] and entree['MonitoredVehicleJourney']['JourneyNote'][0]['value'] != "":
                destination = f"{entree['MonitoredVehicleJourney']['JourneyNote'][0]['value']} | {destination}"

            if attente >= 0:
                line.get_stop(id_arret).add_timetable_record(destination, attente)

        return station
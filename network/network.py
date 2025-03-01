from abc import abstractmethod, ABC

from database.database_gtfs import DatabaseGTFS
from model.station import Station


class Network(ABC):
    def __init__(self, name: str, schema: str):
        self.name = name
        self._database = DatabaseGTFS(schema)

    def get_stations(self, stop_name: str) -> list[str]:
        return self._database.get_stations(stop_name)

    def get_stop_name(self, stop_id: str) -> str:
        return self._database.get_stop_name(stop_id)

    def get_lines(self, ligne: str) -> list[str]:
        return self._database.get_lines(ligne)

    @abstractmethod
    def create_station(self, station_id: str) -> Station:
        pass

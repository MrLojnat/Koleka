from abc import ABC

from database.database import Database
from abc import ABC


class DatabaseUsers(ABC):
    def __init__(self):
        self.__schema_name = "User"

    def add_favori(self, user_id: int, station_id: str, network: str) -> None:
        with Database(self.__schema_name) as database:
            database.execute('''INSERT INTO favorites(user_id, station_id, network) VALUES (?, ?, ?)''', (user_id, station_id, network))

    def remove_favori(self, user_id: int, station_id: str, network: str) -> None:
        with Database(self.__schema_name) as database:
            database.execute('''DELETE FROM favorites WHERE user_id = ? AND station_id = ?''', (user_id, station_id, network,))

    def get_favoris(self, user_id: int, network: str) -> list[str]:
        with Database(self.__schema_name) as database:
            rows = database.query('''SELECT station_id from favorites where user_id = ? and network = ?''', (str(user_id), network,))
        return None if not rows else [i[0] for i in rows]

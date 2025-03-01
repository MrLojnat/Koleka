from abc import ABC

from database.database import Database


class DatabaseGTFS(ABC):
    def __init__(self, schema_name):
        self.__schema_name = schema_name

    def get_stations(self, stop_name: str) -> list:
        with Database(self.__schema_name) as database:
            return database.query('''
                SELECT DISTINCT s.stop_id, s.stop_name, MATCH(s.stop_name) AGAINST (%s IN NATURAL LANGUAGE MODE) AS relevance
                FROM stops AS s
                WHERE parent_station IS NULL AND '3' > 0
                ORDER BY relevance DESC
                LIMIT 5''', (stop_name,))

    def get_similar_stations(self, stop_id: str):
        with Database(self.__schema_name) as database:
            rows = [i[0] for i in database.query(''' SELECT s.stop_id FROM stops AS s WHERE s.stop_name = (SELECT s2.stop_name FROM stops AS s2 WHERE s2.stop_id = %s)''', (stop_id,))]
        return rows

    def get_color(self, line_id: str) -> hex:
        with Database(self.__schema_name) as database:
            database.execute('''SELECT route_color FROM routes as R WHERE route_id = %s''', (line_id,))
            row = database.fetchone()

        return 0x2F3136 if not row else int(row[0], 16)

    def get_stop_name(self, stop_id: str) -> str:
        with Database(self.__schema_name) as database:
            database.execute('''SELECT stop_name FROM stops WHERE stop_id = %s;''', (stop_id,))
            row = database.fetchone()

        return " " if not row else row[0]

    def get_lines(self, line_name: str) -> list[str]:
        with Database(self.__schema_name) as database:
            rows = database.query('''SELECT route_id FROM routes WHERE route_short_name = %s OR route_long_name = %s''', (line_name, line_name,))

        return [i[0] for i in rows]

    def get_line_name(self, line_id: str) -> str:
        with Database(self.__schema_name) as database:
            database.execute('''SELECT route_short_name FROM routes WHERE route_id = %s''', (line_id,))
            row = database.fetchone()

        return None if not row else row[0]

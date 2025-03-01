from typing import overload

from sortedcontainers import SortedSet

from model.stop import Stop


class Line:
    def __init__(self, line_id: str, name: str, color: str):
        self.__id = line_id
        self.__name = name
        self.__color = color
        self.__stops: SortedSet[Stop] = SortedSet(key=lambda stop: stop.id)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Line) and self.id == other.id

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def color(self) -> hex:
        return self.__color

    @property
    def stops(self) -> list[Stop]:
        return list(self.__stops)

    @overload
    def get_stop(self, param: int = 0) -> Stop:
        ...

    @overload
    def get_stop(self, param: str) -> Stop:
        ...

    def get_stop(self, param = 0) -> Stop:
        """Donne un arrêt à l'indice donné ou à la correspondance de son nom"""
        if isinstance(param, int):
            return self.stops[param]
        if isinstance(param, str):
            return next((x for x in self.stops if x.id == param), None)

    def add_stop(self, stop_id: str, stop_name: str) -> None:
        """Ajoute un arrêt"""
        arret = Stop(stop_id, stop_name)
        self.__stops.add(arret)

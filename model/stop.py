class Stop:
    def __init__(self, stop_id: str, stop_name: str):
        self.__id = stop_id
        self.__name = stop_name.title()
        self.__timetable: dict[str, list[int]] = {}

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Stop) and self.id == other.id

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def timetable(self) -> dict[str, list[int]]:
        return self.__timetable

    def add_timetable_record(self, destination: str, attente: int):
        """Ajoute un horaire à la destination"""
        self.__timetable.setdefault(destination, []).append(attente)

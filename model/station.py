from typing import overload

import discord
from sortedcontainers import SortedSet

from model.line import Line


class Station:
    def __init__(self, station_id: str, station_name: str):
        self.__id: str = station_id
        self.__name: str = station_name.title()
        self.__lines: SortedSet[Line] = SortedSet(key=lambda line: line.id)

    @property
    def id(self) -> str:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def lines(self) -> list[Line]:
        return list(self.__lines)

    @lines.setter
    def lines(self, value):
        self.__lines = value

    @overload
    def get_line(self, param: int = 0) -> Line | None:
        ...

    @overload
    def get_line(self, param: str) -> Line | None:
        ...

    def get_line(self, param=0) -> Line | None:
        """Donne une ligne à l'indice donné ou à son identifiant"""
        if not self.__lines:
            return None
        if isinstance(param, int):
            param %= len(self.__lines)
            return self.__lines[param % len(self.__lines)]
        if isinstance(param, str):
            return next((x for x in self.__lines if x.id == param), None)

    def add_line(self, line: Line) -> Line:
        """Ajoute une ligne"""
        self.__lines.add(line)
        return line

    def get_line_index(self, line_id: str) -> int:
        """Donne l'indice dans la liste en correspondance avec son nom"""
        try:
            id_lignes_arret = [x.id for x in self.__lines]
            return id_lignes_arret.index(line_id)
        except (ValueError, IndexError, AttributeError):
            return 0

    def get_station_embed(self, num_page: int = 0) -> discord.Embed:
        """Fournit un embed montrant le temps d'attente pour un arrêt et une station donnée"""
        line: Line = self.get_line(num_page)

        embed = discord.Embed(title=f"{line.name} | **Horaires**", color=line.color)
        embed.set_footer(text=f"Page {num_page + 1}/{len(self.__lines)}")

        for stop in line.stops:
            if f"**{stop.name or self.name}**" not in [x.value for x in embed.fields]:
                embed.add_field(name="‎", value=f"**{stop.name}**", inline=False)

            horaires = stop.timetable.items()
            horaires_inline = len(horaires) < 2

            for destination, wait_time in horaires:
                wait_time = [i for i in wait_time[:3] if i <= 60]
                if not wait_time:
                    continue
                elif f"**{stop.name}**" not in [x.value for x in embed.fields]:
                    embed.add_field(name=f"→ {destination}",
                                    value=" min, ".join(map(str, wait_time)) + " min",
                                    inline=horaires_inline)
                else:
                    embed.insert_field_at([x.value for x in embed.fields].index(f"**{stop.name}**") + 1,
                                          name=f"→ {destination}",
                                          value=" min, ".join(map(str, wait_time)) + " min",
                                          inline=horaires_inline)

        if len(embed.fields) < 2:
            embed.add_field(name="Aucun départ", value="...")

        return embed
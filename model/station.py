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

    def get_line_index(self, line_id: str):
        """Donne l'indice dans la liste en correspondance avec son nom"""
        try:
            id_lignes_arret = [x.id for x in self.__lines]
            return id_lignes_arret.index(line_id)
        except (ValueError, IndexError, AttributeError):
            return 0

    def get_station_embed(self, num_page: int = 0) -> discord.Embed:
        """Fournit un embed montrant le temps d'attente pour un arrêt et une station donnée"""
        ligne = self.get_line(num_page)

        embed = discord.Embed(title=f"{ligne.name} | **Horaires**", color=ligne.color)
        embed.set_footer(text=f"Page {num_page + 1}/{len(self.__lines)}")

        for arret in ligne.stops:
            if f"**{arret.name or self.name}**" not in [x.value for x in embed.fields]:
                embed.add_field(name="‎", value=f"**{arret.name}**", inline=False)

            horaires = arret.timetable.items()
            horaires_inline = True if (len(horaires) < 2) else False

            for destination, temps in horaires:
                temps = [i for i in temps[:3] if i <= 60]
                if not temps:
                    continue
                elif f"**{arret.name}**" not in [x.value for x in embed.fields]:
                    embed.add_field(name=f"→ {destination}",
                                    value=" min, ".join(map(str, temps)) + " min",
                                    inline=horaires_inline)
                else:
                    embed.insert_field_at([x.value for x in embed.fields].index(f"**{arret.name}**") + 1,
                                          name=f"→ {destination}",
                                          value=" min, ".join(map(str, temps)) + " min",
                                          inline=horaires_inline)

        if len(embed.fields) < 2:
            embed.add_field(name="Aucun départ", value="...")

        return embed
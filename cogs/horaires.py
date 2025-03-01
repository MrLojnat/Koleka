import asyncio
import traceback
from abc import ABC
from typing import Optional

import discord
from discord import app_commands
from discord.app_commands import Group
from discord.ext import commands
from discord.ui import Select, View

from database.database_users import DatabaseUsers
from model.station import Station
from network.network import Network
from network.networks import Networks


# Embeds Discord
def embed_ratp(description=None, couleur=0x2F3136) -> discord.Embed:
    """Retourne un embed de type RATK (même titre ; description et couleurs pouvant être choisies)
    :return: Embed avec emoji RATK, la description et la couleur données
    """
    return discord.Embed(title="<:ratk:697886113196671058> | **Horaires**",
                         description=description,
                         color=couleur)

async def affiche_embed(interaction: discord.Interaction, titre: str) -> None:
    """Affiche un embed"""
    embed = embed_ratp(titre)
    await interaction.edit_original_response(embed=embed)
    await asyncio.sleep(3)
    await interaction.delete_original_response()


async def chargement(interaction: discord.Interaction) -> None:
    """Affiche un embed de chargement"""
    await interaction.response.send_message(embed=CHARGEMENT)


# Constantes
EMOJI_NON = "<:non:1345525249076367462>"
EMOJI_OUI = "<:oui:1345524782493466797>"
EMOJI_CHARGEMENT = "<a:chargement:1345525475912581191>"

IDFM_INDISPONIBILITE = f"{EMOJI_NON} | **Indisponibilité des données fournies**"
CHARGEMENT = embed_ratp(f"{EMOJI_CHARGEMENT} | **Chargement ...**")
CHIFFRES = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
LIGNES = [["A", "B", "C", "D", "E"],
          ["H", "J", "K", "L", "N", "P", "R", "U"],
          ["1", "2", "3", "3B", "4", "5", "6", "7", "7B", "8", "9", "10", "11", "12", "13", "14"],
          ["T1", "T2", "T3a", "T3b", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T13"]]


async def station_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Retourne une liste des choix correspondant à la frappe de l'utilisateur

    :param interaction: Interaction discord associée
    :param current: Champ que l'utilisateur est en train de saisir
    :return: Liste de choix possibles correspondant à ce que l'utilisateur a entré
    """
    print(interaction.data)
    network_name: str = interaction.data['options'][0]['options'][0]['value']
    network: Network = Networks.network(network_name)

    stations_names: list[str] = []
    stations: list[str] = []

    if len(current) == 0:
        stations = DatabaseUsers().get_favoris(interaction.user.id, network.name)
        stations_names = [network.get_stop_name(i).title() for i in stations]
        stations = ["id:" + i for i in stations]
    elif len(stations) == 0:
        stations = network.get_stations(current)
        stations_names = [f"{stop[1].title()}, {stop[2]}" if len(stop) > 14 else stop[1].title() for stop in stations]
        stations = ["id:" + i[0] for i in stations]

    return [
        app_commands.Choice(name=station, value=stations[i])
        for i, station in enumerate(stations_names) if current.lower() in station.lower()
    ]


class Horaires(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print("Module Transport chargé")

    async def choix_ville(self, arrets_choix: list, interaction_choix: discord.Interaction) -> int:
        select = Select()

        for i, arret in enumerate(arrets_choix):
            select.append_option(discord.SelectOption(value=str(i),
                                                      label=f"{arret[2]}, {arret[14] if len(arret) > 14 else arret[2]}"))

        await interaction_choix.edit_original_response(view=View().add_item(select))
        await self.bot.wait_for('interaction')

        return int(select.values[0])

    @staticmethod
    async def initialiser_arret(stop: str, network: Network) -> str | None:
        if "id:" in stop:
            return stop[3:]

        stops = network.get_stations(stop)
        return stops[0] if stops else None


    g_horaires = Group(name='horaires', description='description')
    g_favoris = Group(parent=g_horaires, name='favori', description='description')

    @g_horaires.command(name="chercher", description="Horaires du réseau francilien")
    @app_commands.rename(network_name="réseau")
    @app_commands.choices(network_name=Networks.choices())
    @app_commands.rename(stop_name="arrêt")
    @app_commands.autocomplete(stop_name=station_autocomplete)
    @app_commands.describe(stop_name="Nom de l'arrêt")
    @app_commands.rename(line="ligne")
    @app_commands.describe(line="Ligne voulue (optionnel)")
    async def horaires(self, interaction: discord.Interaction, network_name: app_commands.Choice[str], stop_name: str, line: Optional[str]):
        await chargement(interaction)

        network: Network = Networks.network(network_name.value)
        stop_id: str = await self.initialiser_arret(stop_name, network)

        if not stop_id:
            await affiche_embed(interaction, f"{EMOJI_NON} | **Station non trouvée**")

        # Si il y a des problèmes au niveau de l'API
        try:
            station: Station = network.create_station(stop_id)
        except Exception:
            traceback.print_exc()
            await affiche_embed(interaction, f"{EMOJI_NON} | **Données indisponibles**")
            return

        # S'il n'y a aucun départ à la station
        if not station.lines:
            await affiche_embed(interaction, f"{EMOJI_NON} | **Aucun départ**")
            return

        # Si l'utilisateur a fourni une ligne spécifique, on cherche le numéro de page correspondant à cette ligne

        num_page = station.get_line_index(network.get_lines(line)[0]) if line else 0

        vue = Boutons(interaction, network, station, num_page)
        await interaction.edit_original_response(embed=station.get_station_embed(num_page), view=vue)

    @g_favoris.command(name="ajouter", description="Enregistrer les stations favorites")
    @app_commands.rename(network_name="réseau")
    @app_commands.choices(network_name=Networks.choices())
    @app_commands.rename(stop_name="arrêt")
    @app_commands.autocomplete(stop_name=station_autocomplete)
    @app_commands.describe(stop_name="Nom de l'arrêt")
    async def enregistrer_favori(self, interaction: discord.Interaction, network_name: app_commands.Choice[str], stop_name: str):
        await chargement(interaction)

        network: Network = Networks.network(network_name.value)
        stop_id: str = await self.initialiser_arret(stop_name, network)

        if not stop_id:
            await affiche_embed(interaction, f"{EMOJI_NON} | **Station non trouvée**")
            return

        try:
            DatabaseUsers().add_favori(interaction.user.id, stop_id, network_name.value)
        except Exception as e:
            print(e)
            await affiche_embed(interaction, f"{EMOJI_NON} | **Favori déjà ajouté**")
            return

        await interaction.edit_original_response(embed=embed_ratp(f"{EMOJI_OUI} | **Favori ajouté**"))

    @g_favoris.command(name="supprimer", description="Supprimer une station favorite")
    @app_commands.choices(network_name=Networks.choices())
    @app_commands.rename(stop_name="arrêt")
    @app_commands.autocomplete(stop_name=station_autocomplete)
    @app_commands.describe(stop_name="Nom de l'arrêt")
    async def supprimer_favori(self, interaction: discord.Interaction, network_name: app_commands.Choice[str], stop_name: str):
        await chargement(interaction)

        DatabaseUsers().remove_favori(interaction.user.id, stop_name, network_name.value)

        try:
            await affiche_embed(interaction, f"{EMOJI_OUI} | **Favori supprimé**")
        except Exception as e:
            print(e)
            await affiche_embed(interaction, f"{EMOJI_NON} | **Favori invalide ou non existant**")

    @g_favoris.command(name="liste", description="Voir votre liste de stations favorites")
    @app_commands.choices(network_name=Networks.choices())
    async def voir_favori(self, interaction: discord.Interaction, network_name: app_commands.Choice[str]):
        await chargement(interaction)

        network: Network = Networks.network(network_name.value)

        favoris = DatabaseUsers().get_favoris(interaction.user.id, network_name.value)
        favoris = [f' • {network.get_stop_name(i).title()} \n' for i in favoris]
        await interaction.edit_original_response(embed=embed_ratp(''.join(favoris)))


class Boutons(ABC, discord.ui.View):
    def __init__(self, interaction: discord.Interaction, network: Network, station: Station, num_page: int):
        super().__init__(timeout=1200)
        self.interaction = interaction
        self.network = network
        self.station = station
        self.num_page = num_page
        self.num_direction = 0
        self.max = len(station.lines)

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.gray)
    async def page_precedente(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.num_page = (self.num_page - 1) % self.max
        await self.refresh(interaction)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.grey)
    async def page_suivante(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.num_page = (self.num_page + 1) % self.max
        await self.refresh(interaction)

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.grey)
    async def recharger(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.station = self.network.create_station(self.station.id)
        await self.refresh(interaction)

    async def refresh(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.edit_original_response(embed=self.station.get_station_embed(self.num_page))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.interaction.edit_original_response(view=self)

async def setup(bot: commands.Bot):
    await bot.add_cog(Horaires(bot))

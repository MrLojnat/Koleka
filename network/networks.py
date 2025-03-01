from enum import Enum

from discord import app_commands

from network.idfm import IDFM
from network.network import Network


class Networks(Enum):
    IDFM = IDFM()

    @classmethod
    def choices(cls):
        return [app_commands.Choice(name=network.value.name, value=network.name) for network in cls]

    @classmethod
    def network(cls, network_name: str) -> Network:
        return cls[network_name].value
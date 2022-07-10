import typing
from dataclasses import dataclass


@dataclass
class PreparationPluginReturn(object):
    success: bool
    messages: typing.List[str]

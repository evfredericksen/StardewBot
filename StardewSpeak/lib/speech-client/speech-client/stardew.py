import time
import async_timeout
import contextlib
import traceback
import weakref
import functools
import queue
import sys
import asyncio
import threading
import uuid
import json
from dragonfly import *
from srabuilder import rules

from srabuilder.actions import directinput
import constants, server, game, objective, locations


direction_keys = {
    "north": "w",
    "main": "wd",
    "east": "d",
    "floor": "ds",
    "south": "s",
    "air": "as",
    "west": "a",
    "wash": "aw",
}
direction_nums = {
    "north": 0,
    "east": 1,
    "south": 2,
    "west": 3,
}
nums_to_keys = {
    0: "w",
    1: "d",
    2: "s",
    3: "a",
}
directions = {k: k for k in direction_keys}
tools = {
    "axe": constants.AXE,
    "hoe": constants.HOE,
    "pickaxe": constants.PICKAXE,
    "scythe": constants.SCYTHE,
    "watering can": constants.WATERING_CAN,
}
repeat_mapping = {}

npcs = {
    'abigail': constants.ABIGAIL,
    'alex': constants.ALEX,
    'caroline': constants.CAROLINE,
    'demetrius': constants.DEMETRIUS,
    'elliott': constants.ELLIOTT,
    'emily': constants.EMILY,
    'gus': constants.GUS,
    'haley': constants.HALEY,
    'harvey': constants.HARVEY,
    'jas': constants.JAS,
    'jodi': constants.JODI,
    'kent': constants.KENT,
    'leah': constants.LEAH,
    'lewis': constants.LEWIS,
    'marnie': constants.MARNIE,
    'muh roo': constants.MARU,
    'pam': constants.PAM,
    'penny': constants.PENNY,
    'pierre': constants.PIERRE,
    'robin': constants.ROBIN,
    'sam': constants.SAM,
    'sebastian': constants.SEBASTIAN,
    'shane': constants.SHANE,
    'vincent': constants.VINCENT,
    'willy': constants.WILLY,
}


numrep2 = Sequence(
    [Choice(None, rules.nonZeroDigitMap), Repetition(Choice(None, rules.digitMap), min=0, max=10)],
    name="n2",
)
num2 = Modifier(numrep2, rules.parse_numrep)

def rule_builder():
    builder = rules.RuleBuilder()
    builder.basic.append(
        rules.ParsedRule(
            mapping=non_repeat_mapping,
            name="stardew_non_repeat",
            extras=[
                rules.num,
                num2,
                Choice("direction_keys", direction_keys),
                Choice("direction_nums", direction_nums),
                Choice("directions", directions),
                Choice("tools", tools),
                Choice("npcs", npcs),
                Choice("locations", locations.location_commands(locations.locations))
            ],
            defaults={"n": 1},
        )
    )
    # builder.repeat.append(
    #     rules.ParsedRule(mapping=repeat_mapping, name="stardew_repeat")
    # )
    return builder


def objective_action(objective_cls, *args):
    format_args = lambda **kw: [objective_cls(*[kw[a] for a in args])]
    return server.AsyncFunction(objective.new_active_objective, format_args=format_args)


non_repeat_mapping = {
    "<direction_keys>": objective_action(objective.HoldKeyObjective, "direction_keys"),
    "face <direction_nums>": objective_action(objective.FaceDirectionObjective, "direction_nums"),
    "stop": server.AsyncFunction(objective.cancel_active_objective, format_args=lambda **kw: []),
    "swing": Function(lambda: directinput.send("c")),
    "(action|check)": Function(lambda: directinput.send("x")),
    "(escape | menu)": Function(lambda: directinput.send("esc")),
    "<n> <directions>": objective_action(objective.MoveNTilesObjective, "directions", "n"),
    "go to mailbox": objective_action(objective.MoveToPointObjective),
    "go to <locations>": objective_action(objective.MoveToLocationObjective, "locations"),
    "start chopping trees": objective_action(objective.ChopTreesObjective),
    "water crops": objective_action(objective.WaterCropsObjective),
    "clear debris": objective_action(objective.ClearDebrisObjective),
    "hoe <n> by <n2>": objective_action(objective.HoePlotObjective, "n", "n2"),
    "equip <tools>": server.AsyncFunction(game.equip_item, format_args=lambda **kw: [kw['tools']]),
    "talk to <npcs>": objective_action(objective.TalkToNPCObjective, "npcs"),
}
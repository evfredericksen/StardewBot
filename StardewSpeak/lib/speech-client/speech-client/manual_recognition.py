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

class Commands:

    def __init__(self):
        self.named_rules = {}
        self.commands = []
        self.words = []
        self.last_recognition_timestamp = time.time()

    def add_command(self, spec, action, end_silence=0):
        parsed_spec = parse_spec(spec)
        self.commands.append((parsed_spec, action, end_silence))

    def add_named_rule(self, name: str, rule):
        self.named_rules[name] = rule

    def build_mapping(self):
        mapping = {}
        for parsed_spec, action, end_silence in self.commands:
            for item in parsed_spec:
                item_type = item['type']
                if item_type == 'word':
                    mapping[item['value']] = Function(wrapped_partial(self.on_recognition, item['value']))
                elif item_type == 'ruleRef':
                    for word in self.named_rules[item['value']]:
                        mapping[word] = Function(wrapped_partial(self.on_recognition, word))
        print(mapping)
        return mapping

    def on_recognition(self, word):
        now = time.time()
        if self.last_recognition_timestamp and now - self.last_recognition_timestamp > 0.5:
            self.words = []
        self.last_recognition_timestamp = now
        self.words.append(word)
        result = self.match_command(self.words)
        if result is not None:
            match_args, action, end_silence = result
            self.words = []
            server.call_soon(action, *match_args)

    def match_command(self, words):
        for parsed_spec, action, end_silence in self.commands:
            try:
                match_args = self.spec_matches(parsed_spec, self.words, self.named_rules)
            except SpecMatchFail:
                continue
            else:
                return match_args, action, end_silence 

    def spec_matches(self, spec, words, named_rules):
        match_args = []
        for i, node in enumerate(spec):
            try:
                current_word = words[i]
            except IndexError:
                raise SpecMatchFail()
            ntype = node['type']
            if ntype == 'word':
                if node['value'] != current_word:
                    raise SpecMatchFail()
                continue
            elif ntype == 'ruleRef':
                rule_mapping = named_rules[node['value']]
                if current_word not in rule_mapping:
                    raise SpecMatchFail()
                match_args.append(rule_mapping[current_word])
            else:
                raise ValueError(f'Unknown node type {ntype}')
        return match_args

class SpecMatchFail(Exception):
    pass

class Match:

    def __init__(self):
        pass


def wrapped_partial(func, *args, **kwargs):
    partial_func = functools.partial(func, *args, **kwargs)
    functools.update_wrapper(partial_func, func)
    return partial_func

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

class RecognizeWord(ActionBase):
    pass


async def some_action(direction):
    await asyncio.sleep(1)
    print(direction)
    await asyncio.sleep(1)
    print('done')


def parse_spec(spec: str):
    parsed = []
    parsing_rule = False
    text = ''
    print(spec)
    for i, char in enumerate(spec):
        if char.isalpha():
            text += char
        elif char == '<':
            if parsing_rule:
                raise RuntimeError('Already parsing rule')
            parsing_rule = True
        elif char == '>': 
            if not parsing_rule:
                raise RuntimeError('Invalid rule close token')
            if not text:
                raise RuntimeError('Empty rule')
            parsed.append({'type': 'ruleRef', 'value': text})
            text = ''
            parsing_rule = False
        elif char == ' ':
            if text:
                parsed.append({'type': 'word', 'value': text})
                text = ''
        else:
            raise RuntimeError(f'Invalid character: {char}')
    if parsing_rule:
        raise RuntimeError('Unclosed rule')
    if text:
        parsed.append({'type': 'word', 'value': text})
    print(parsed)
    return parsed

non_repeat_mapping = {
    "go <direction>": some_action,
}

def rule_builder():
    commands = Commands()
    commands.add_named_rule('directions', directions)
    commands.add_command('go <directions>', some_action)
    mapping = commands.build_mapping()
    builder = rules.RuleBuilder()
    builder.basic.append(
        MappingRule(
            mapping=mapping,
            name="stardew_non_repeatt",
            # extras=[
            #     rules.num,
            #     num2,
            #     Choice("direction_keys", direction_keys),
            #     Choice("direction_nums", direction_nums),
            #     Choice("directions", directions),
            #     Choice("tools", tools),
            #     Choice("npcs", npcs),
            #     Choice("locations", locations.location_commands(locations.locations))
            # ],
            defaults={"n": 1},
        )
    )
    return builder


def objective_action(objective_cls, *args):
    format_args = lambda **kw: [objective_cls(*[kw[a] for a in args])]
    return server.AsyncFunction(objective.new_active_objective, format_args=format_args)

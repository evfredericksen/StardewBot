from srabuilder.actions import pydirectinput
import dragonfly as df
import server
import time
import df_utils

letter_map = {
    "(alpha)": "a",
    "(bravo) ": "b",
    "(charlie) ": "c",
    "(danger) ": "d",
    "(eureka) ": "e",
    "(foxtrot) ": "f",
    "(gorilla) ": "g",
    "(hotel) ": "h",
    "(india) ": "i",
    "(juliet) ": "j",
    "(kilo) ": "k",
    "(lima) ": "l",
    "(michael) ": "m",
    "(november) ": "n",
    "(Oscar) ": "o",
    "(papa) ": "p",
    "(quiet) ": "q",
    "(romeo) ": "r",
    "(sierra) ": "s",
    "(tango) ": "t",
    "(uniform) ": "u",
    "(victor) ": "v",
    "(whiskey) ": "w",
    "(x-ray) ": "x",
    "(yankee) ": "y",
    "(zulu) ": "z",
}

capital_letter_map = {f"(capital | upper | uppercase) {k}": v.upper() for k, v in letter_map.items()}

keys = {
    "backspace": "backspace",
    "space": "space",
}

def multiply_keys(rep):
    n = 1 if rep[0] is None else rep[0]
    key = rep[1]
    return [key for i in range(n)]

def flatten_list(rep):
    flattened = []
    for l in rep:
        flattened.extend(l)
    return flattened

letters_and_keys_choice = df.Choice(None, {**letter_map, **capital_letter_map, **keys})
letters_and_keys_num = df.Modifier(df.Sequence([df.Optional(df_utils.positive_num, default=1), letters_and_keys_choice]), multiply_keys) 

letters_rep = df.Repetition(letters_and_keys_num, name="letters_and_keys", min=1, max=16)
letters_and_keys = df.Modifier(letters_rep, flatten_list)

def type_letters(letters: str):
    shift_down = False
    for char in letters:
        shift_char = char.isupper()
        char = char.lower()
        if shift_char and not shift_down:
            pydirectinput.keyDown('shift')
            shift_down = True
        elif not shift_char and shift_down:
            pydirectinput.keyUp('shift')
            shift_down = False
        pydirectinput.press(char)
    if shift_down:
        pydirectinput.keyUp('shift')
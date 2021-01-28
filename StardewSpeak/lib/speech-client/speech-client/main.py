"""
Command-module loader for Kaldi.

This script is based on 'dfly-loader-wsr.py' written by Christo Butcher and
has been adapted to work with the Kaldi engine instead.

This script can be used to look for Dragonfly command-modules for use with
the Kaldi engine. It scans the directory it's in and loads any ``_*.py`` it
finds.
"""


# TODO Have a simple GUI for pausing, resuming, cancelling and stopping
# recognition, etc

import os.path
import os
import threading
import time
import logging
import sys

from dragonfly import RecognitionObserver, get_engine, AppContext
from dragonfly.log import setup_log
from srabuilder import sleep, environment
import srabuilder

import stardew, server, manual_recognition


# --------------------------------------------------------------------------
# Simple recognition observer class.


class Observer(RecognitionObserver):
    def on_begin(self):
        return
        print("Speech started.")

    def on_recognition(self, words):
        print("Recognized:", " ".join(words))

    def on_failure(self):
        return
        print("Sorry, what was that?")


def command_line_loop(engine):
    while True:
        user_input = input("> ")
        if user_input:
            time.sleep(4)
            try:
                engine.mimic(user_input)
            except Exception as e:
                print(e)


# --------------------------------------------------------------------------
# Main event driving loop.


def main(args):
    logging.basicConfig(level=logging.INFO)
    engine = srabuilder.setup_engine(silence_timeout=0)

    # Register a recognition observer
    observer = Observer()
    observer.register()

    sleep.load_sleep_wake_grammar(True)
    startdew_context = AppContext(title="stardew")
    server.setup_async_loop()
    map_contexts_to_builder = {
        # (startdew_context,): stardew.rule_builder(),
        (): manual_recognition.rule_builder(),
    }
    srabuilder.load_environment_grammars(map_contexts_to_builder)

    # threading.Thread(target=command_line_loop, args=(engine,), daemon=True).start()
    srabuilder.run_engine()


if __name__ == "__main__":
    main(sys.argv[1:])

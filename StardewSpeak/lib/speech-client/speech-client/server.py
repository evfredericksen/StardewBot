import time
import async_timeout
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

# from actions import directinput
from srabuilder.actions import directinput, pydirectinput
import constants

loop = None
streams = {}
mod_requests = {}

ongoing_tasks = {} # not connected to an objective, slide mouse, swing tool etc

async def start_ongoing_task(name, str, async_fn):
    await stop_ongoing_task(name)
    task_wrapper = TaskWrapper(async_fn())
    ongoing_tasks[task]
    

async def stop_ongoing_task(name):
    task = ongoing_tasks.get(name)
    if task:
        await task.cancel()
        del ongoing_tasks[name]
class Stream:
    def __init__(self, name, data=None):
        self.has_value = False
        self.latest_value = None
        self.future = loop.create_future()
        self.name = name
        self.id = f"{name}_{str(uuid.uuid4())}"
        self.closed = False
        self.open(data)

    def set_value(self, value):
        self.latest_value = value
        self.has_value = True
        try:
            self.future.set_result(None)
        except asyncio.InvalidStateError:
            pass

    def open(self, data):
        streams[self.id] = self
        send_message(
            "NEW_STREAM",
            {
                "name": self.name,
                "stream_id": self.id,
                "data": data,
            },
        )

    def close(self):
        if not self.closed:
            self.closed = True
            send_message("STOP_STREAM", self.id)
            del streams[self.id]
            self.set_value(None)

    async def current(self):
        if self.has_value:
            return self.latest_value
        return await self.next()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    async def next(self):
        if self.closed:
            raise StreamClosedError("Stream is already closed")
        if not self.future.done():
            await self.future
        if self.closed:
            raise StreamClosedError(f"Stream {self.name} closed while waiting for next value")
        self.future = loop.create_future()
        return self.latest_value


    async def wait(self, condition, timeout=None):
        async with async_timeout.timeout(timeout):
            item = await self.current()
            while not condition(item):
                item = await self.next()
            return item

class StreamClosedError(Exception):
    pass

def player_status_stream(ticks=1):
    return Stream("UPDATE_TICKED", data={"state": "PLAYER_STATUS", "ticks": ticks})

def tool_status_stream(ticks=1):
    return Stream("UPDATE_TICKED", data={"state": "TOOL_STATUS", "ticks": ticks})

def characters_at_location_stream(ticks=1):
    return Stream("UPDATE_TICKED", data={"state": "CHARACTERS_AT_LOCATION", "ticks": ticks})

def player_items_stream(ticks=1):
    return Stream("UPDATE_TICKED", data={"state": "PLAYER_ITEMS", "ticks": ticks})

def on_warped_stream(ticks=1):
    return Stream("ON_WARPED", data={"state": "PLAYER_STATUS", "ticks": ticks})

def on_terrain_feature_list_changed_stream():
    return Stream("ON_TERRAIN_FEATURE_LIST_CHANGED", data={})

def on_menu_changed_stream():
    return Stream("ON_MENU_CHANGED", data={})

def create_stream_next_task(awaitable):
    async def to_call(awaitable):
        try:
            return await awaitable
        except ValueError as e:
            pass

    return loop.create_task(to_call(awaitable))



class AsyncFunction(ActionBase):
    def __init__(self, async_fn, format_args=None):
        super().__init__()
        self.async_fn = async_fn
        self.format_args = format_args

    async def to_call(self, *a, **kw):
        try:
            await self.async_fn(*a, **kw)
        except (Exception, asyncio.CancelledError, asyncio.TimeoutError) as e:
            log(traceback.format_exc())

    def execute(self, data=None):
        assert isinstance(data, dict)
        kwargs = {k: v for k, v in data.items() if not k.startswith("_")}
        if self.format_args:
            args = self.format_args(**kwargs)
            return call_soon(self.to_call, *args)
        return call_soon(self.to_call, **kwargs)

class SyncFunction(ActionBase):
    def __init__(self, fn, format_args=None):
        super().__init__()
        self.fn = fn
        self.format_args = format_args

    def execute(self, data=None):
        assert isinstance(data, dict)
        kwargs = {k: v for k, v in data.items() if not k.startswith("_")}
        if self.format_args:
            args = self.format_args(**kwargs)
            return self.fn(*args)
        return self.fn(**kwargs)

def call_soon(awaitable, *args, **kw):
    loop.call_soon_threadsafe(_do_create_task, awaitable, *args, **kw)


def _do_create_task(awaitable, *args, **kw):
    loop.create_task(awaitable(*args, **kw))


def setup_async_loop():
    global loop
    loop = asyncio.new_event_loop()
    def async_setup(l):
        l.set_exception_handler(exception_handler)
        l.create_task(menu_changed())
        l.create_task(async_readline())
        l.create_task(heartbeat(3600))
        l.run_forever()

    def exception_handler(loop, context):
        # This only works when there are no references to the above tasks.
        # https://bugs.python.org/issue39256y'
        get_engine().disconnect()
        raise context["exception"]

    async_thread = threading.Thread(target=async_setup, daemon=True, args=(loop,))
    async_thread.start()

async def menu_changed():
    async with on_menu_changed_stream() as stream:
        while True:
            changed_event = await stream.next()

async def heartbeat(timeout):
    while True:
        fut = request("HEARTBEAT")
        try:
            resp = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError as e:
            raise e
        await asyncio.sleep(timeout)


async def async_readline():
    # Is there a better way to read async stdin on Windows?
    q = queue.Queue()

    def _run(future_queue):
        while True:
            fut = future_queue.get()
            line = sys.stdin.readline()
            loop.call_soon_threadsafe(fut.set_result, line)

    threading.Thread(target=_run, daemon=True, args=(q,)).start()
    while True:
        fut = loop.create_future()
        q.put(fut)
        line = await fut
        on_message(line)


def request(msg_type, msg=None):
    sent_msg = send_message(msg_type, msg)
    fut = loop.create_future()
    mod_requests[sent_msg["id"]] = fut
    return fut


def send_message(msg_type, msg=None):
    msg_id = str(uuid.uuid4())
    full_msg = {"type": msg_type, "id": msg_id, "data": msg}
    print(json.dumps(full_msg), flush=True)
    return full_msg


def on_message(msg_str):
    try:
        msg = json.loads(msg_str)
    except json.JSONDecodeError:
        log(f"Got invalid message from mod {msg_str}")
        return
    msg_type = msg["type"]
    msg_data = msg["data"]
    if msg_type == "RESPONSE":
        fut = mod_requests.pop(msg_data["id"], None)
        if fut:
            resp_value = msg_data["value"]
            try:
                fut.set_result(resp_value)
            except asyncio.InvalidStateError:
                pass
    elif msg_type == "STREAM_MESSAGE":
        stream_id = msg_data["stream_id"]
        stream = streams.get(stream_id)
        if stream is None:
            log(f"Can't find {stream_id}")
            send_message("STOP_STREAM", stream_id)
            return
        stream.set_value(msg_data["value"])
        stream.latest_value = msg_data["value"]
        try:
            stream.future.set_result(None)
        except asyncio.InvalidStateError:
            pass
    elif msg_type == "ON_EVENT":
        handle_event(msg_data["eventType"], msg_data["data"])
    else:
        raise RuntimeError(f"Unhandled message type from mod: {msg_type}")

async def set_mouse_position(x: int, y: int):
    await request('SET_MOUSE_POSITION', {'x': x, 'y': y})

async def set_mouse_position_relative(x: int, y: int):
    await request('SET_MOUSE_POSITION_RELATIVE', {'x': x, 'y': y})

async def mouse_click(btn='left'):
    await request('MOUSE_CLICK', {'btn': btn})

def handle_event(event_type, data):
    if event_type == "ON_WARPED":
        game_state.last_warp = data


def log(*a, sep=' '):
    to_send = [x if isinstance(x, str) else json.dumps(x) for x in a]
    return send_message("LOG", sep.join(to_send))

async def sleep_forever():
    while True:
        await asyncio.sleep(3600)

async def cancel_task(task):
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


class TaskWrapper:

    def __init__(self, coro):
        self.result = None
        self.exception = None
        self.done = False
        self.task = loop.create_task(self.wrap_coro(coro))

    # I don't understand asyncio task exception handling. So let's just catch any coroutine exceptions here and expose
    # the result/exception through self.result and self.exception
    async def wrap_coro(self, coro):
        try:
            self.result = await coro
        except (asyncio.CancelledError, Exception) as e:
            self.exception = e
        self.done = True

    async def cancel(self):
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
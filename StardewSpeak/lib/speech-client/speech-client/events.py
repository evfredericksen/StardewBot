import constants
import server
import asyncio
import inspect
import collections

def on_key_pressed(data):
    import game
    if data['button'] in game.cardinal_buttons:
        direction = game.buttons_to_directions[data['button']]
        game.set_last_faced_direction(direction)

event_registry = {
    "KEY_PRESSED": on_key_pressed,
    "UPDATE_TICKING": lambda x: None,
    "UPDATE_TICKED": lambda x: None,
}
event_futures = collections.defaultdict(lambda: server.loop.create_future())

async def wait_for_update_ticking():
    return
    return wait_for_event('UPDATE_TICKING')
    
async def wait_for_update_ticked():
    return
    return wait_for_event('UPDATE_TICKED')
    
def wait_for_event(event_name: str):
    return event_futures[event_name]

def handle_event(evt):
    handler = event_registry.get(evt['eventType'])
    assert handler
    if handler:
        if inspect.iscoroutinefunction(handler):
            server.call_soon(handler, evt['data'])
        else:
            handler(evt['data'])
        fut = event_futures[evt['eventType']]
        event_futures[evt['eventType']] = server.loop.create_future()
        fut.set_result(evt['data'])

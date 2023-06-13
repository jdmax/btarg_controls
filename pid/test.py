# Import the basic framework components.
from softioc import softioc, builder, asyncio_dispatcher
import asyncio

dispatcher = asyncio_dispatcher.AsyncioDispatcher()

builder.SetDeviceName("Test")

sevs = {'HHSV': 'MAJOR', 'HSV': 'MINOR', 'LSV': 'MINOR', 'LLSV': 'MAJOR'}

ai = builder.aIn('AI', initial_value=5)
ao = builder.aOut('AO', initial_value=12.45, always_update=True,
                  on_update=lambda v: ai.set(v))

builder.LoadDatabase()
softioc.iocInit(dispatcher)

async def update():
    while True:
        ai.set(ai.get() + 1)
        await asyncio.sleep(1)

dispatcher(update)

softioc.interactive_ioc(globals())
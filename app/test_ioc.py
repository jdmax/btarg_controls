from softioc import softioc, builder, asyncio_dispatcher
import importlib
import asyncio

async def main():

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    builder.SetDeviceName('device_name')

    d = DeviceIOC()
    builder.LoadDatabase()

    softioc.iocInit(dispatcher)
    async def loop():
        while True:
            await d.loop()
    dispatcher(loop)
    softioc.interactive_ioc(globals())

class DeviceIOC():
    def __init__(self):
        self.module = importlib.import_module('test_module')
        self.device = self.module.Device()
    async def loop(self):
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())


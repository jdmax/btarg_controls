from softioc import softioc, builder, asyncio_dispatcher, alarm
import asyncio
import yaml

from app.flow import FlowControl


async def main():

    settings, records = load_settings()

    # Create an asyncio dispatcher, the event loop is now running
    dispatcher = asyncio_dispatcher.AsyncioDispatcher()

    # Set the record prefix
    builder.SetDeviceName("TGT:BTARG")

    # Create some records
    ai = builder.aIn('AI', initial_value=5)
    ai2 = builder.aIn('AI2', initial_value=25)
    ao = builder.aOut('AO', initial_value=12.45, always_update=True,
                      on_update=lambda v: ai.set(v))
    ai.HIHI = 10  
    ai.HIGH = 5 
    ai.LOW = 2  
    ai.LOLO = 1  

    flow = FlowControl(settings, records)

    # Boilerplate get the IOC started
    builder.LoadDatabase()
    softioc.iocInit(dispatcher)
    
    def update_as(v1,v2):
        ai.set(v1)
        ai2.set(v2)

    # Start processes required to be run after iocInit
    async def update():
        while True:
            ai.set(ai.get() + 1)
            await asyncio.sleep(1)
            
    async def update2():
        while True:
            ai2.set(ai2.get() + 1)
            await asyncio.sleep(1)

    dispatcher(update)
    dispatcher(update2)

    # Finally leave the IOC running with an interactive shell.
    softioc.interactive_ioc(globals())


def load_settings():
    '''Load device settings and records from YAML settings file'''

    with open('settings.yaml') as f:                           # Load settings from YAML files
       settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {'settings.yaml'}.")

    with open('records.yaml') as f:                           # Load settings from YAML files
       records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {'records.yaml'}.")
    return settings, records
    
    
if __name__ == "__main__":
    asyncio.run(main())
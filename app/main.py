from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from collections import ChainMap

from flow.flow_ioc import FlowControl


async def main():

    settings, records, pids = load_settings()

    # Create an asyncio dispatcher, the event loop is now running
    dispatcher = asyncio_dispatcher.AsyncioDispatcher()

    # Set the record prefix
    device_name = settings['ioc']['name']
    builder.SetDeviceName(device_name)
    
    # Start up devices, make and attached PVs
    flow = FlowControl(device_name, settings['flow_controller'], records['flow'])
    pvs = ChainMap(flow.pvs)

    # Boilerplate get the IOC started
    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    # Finally leave the IOC running with an interactive shell.
    softioc.interactive_ioc(globals())


def load_settings():
    '''Load device settings and records from YAML settings file'''

    with open('../settings.yaml') as f:                           # Load settings from YAML files
       settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {'settings.yaml'}.")

    with open('../records.yaml') as f:                           # Load settings from YAML files
       records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {'records.yaml'}.")

    with open('../pids.yaml') as f:                           # Load pids from YAML files
       pids = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {'pids.yaml'}.")
    return settings, records, pids
    
    
if __name__ == "__main__":
    asyncio.run(main())
from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
import argparse
import importlib


async def main():
    """
    Run IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    """
    ioc, settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['general']['prefix']
    builder.SetDeviceName(device_name)

    d = DeviceIOC(device_name, settings[ioc], records)
    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    async def loop():
        while True:
            await d.loop()

    dispatcher(loop)  # put functions to loop in here
    softioc.interactive_ioc(globals())


class DeviceIOC():
    """Set up PVs for device IOC, run thread to interact with device
    """

    def __init__(self, device_name, settings, records):
        '''
        Arguments:
            device_name: name of device for PV prefix
            settings: dict of device settings
            records: dict of record settings
        '''

        self.module = importlib.import_module(settings['module'])
        self.records = records
        self.delay = settings['delay']

        self.device = self.module.Device(device_name, settings)
        self.device.connect()

        for name, entry in self.device.pvs.items():  # set the attributes of the PV (optional)
            if name in self.records:
                for field, value in self.records[name]['fields'].items():
                    setattr(self.device.pvs[name], field, value)

    async def loop(self):
        """Read indicator PVS from controller channels. Delay time between measurements is in seconds.
         """
        await asyncio.sleep(self.delay)
        self.device.do_reads()  # get new readings from device and set into PVs


def load_settings():
    """Load device settings and records from YAML settings files.
    Argument parser allows '-s' to give a different folder, '-i' tells which IOC to run"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", help="Settings file folder, default is here.")
    parser.add_argument("-i", help="Name of IOC to start")
    args = parser.parse_args()
    folder = args.s if args.s else '.'

    with open(f'{folder}/settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/settings.yaml.")

    with open(f'{folder}/records.yaml') as f:  # Load settings from YAML files
        records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {folder}/records.yaml.")

    ioc_list = list(settings.keys())
    ioc_list.remove('general')

    if args.i:
        ioc = args.i
    else:
        print("Select IOC to run from these entries in settings file using -i flag:")
        [print(f"  {x}") for x in ioc_list]
        exit()
    if ioc not in ioc_list:
        print("Given IOC not in settings file. Select from these:")
        [print(f"  {x}") for x in ioc_list]
        exit()

    return ioc, settings, records


if __name__ == "__main__":
    asyncio.run(main())

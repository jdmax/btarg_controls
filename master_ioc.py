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
    device_name = settings['all_iocs']['prefix'] + ":" + settings[ioc]['prefix']
    builder.SetDeviceName(device_name)

    d = DeviceIOC(device_name, settings[ioc], records)
    print(repr(d.device.pvs['Coolant_Mode']))
    builder.LoadDatabase()
    print(repr(d.device.pvs['Coolant_Mode']))
    softioc.iocInit(dispatcher)
    async def loop():
        while True:
            await d.loop()
    dispatcher(loop)  # put functions to loop in here
    softioc.interactive_ioc(globals())

class DeviceIOC():
    '''Set up PVs for device IOC, run thread to interact with device
    '''
    def __init__(self, device_name, settings, records):
        '''
        Attributes:
            pvs: list of builder process variables created
        Arguments:
            settings: dict of device settings
            records: dict of record settings
        '''

        self.module = importlib.import_module(settings['module'])
        self.records = records
        self.settings = settings
        self.delay = self.settings['delay']
        self.enable = self.settings['enable']
        self.ticks = 2  # times per seconds to do device sets
        self.tocks = self.delay * self.ticks  # only run reads every tock
        self.i = 0

        self.device = self.module.Device(device_name, self.settings)
        self.device.connect()

        for name, entry in self.device.pvs.items():
            if name in self.records:
                for field, value in self.records[name]['fields'].items():
                    setattr(self.device.pvs[name], field, value)   # set the attributes of the PV

    async def loop(self):
        '''
         Coroutine to read indicator PVS from controller channels. Identifies driver method to use from PV name. Delay time between measurements is in seconds.
         '''
        await asyncio.sleep(1 / self.ticks)
        self.i += 1

        if self.enable:
            self.device.do_sets()  # set changed PVs to device

            if self.i == self.tocks:
                self.device.do_reads()  # get new readings from device
                self.i = 0
            self.device.update_pvs()  # put new readings into PVs


def load_settings():
    """Load device settings and records from YAML settings files.
    Argument parser allows '-s' to give a different folder"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--Settings", help = "Settings file folder")
    parser.add_argument("-i", "--IOC", help = "Name of IOC to start")
    args = parser.parse_args()
    folder = args.Settings if args.Settings else '.'

    with open(f'{folder}/settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/settings.yaml.")

    with open(f'{folder}/records.yaml') as f:  # Load settings from YAML files
        records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {folder}/records.yaml.")

    ioc_list = list(settings.keys())
    ioc_list.remove('all_iocs')

    if args.IOC:
        ioc = args.IOC
    else:
        print("Select IOC to run from these entries in settings file:")
        [print(f"-{x}") for x in ioc_list]
        exit()
    if ioc not in ioc_list:
        print("Given IOC not in settings file. Select from these:")
        [print(f"-{x}") for x in ioc_list]

    return ioc, settings, records


if __name__ == "__main__":
    asyncio.run(main())



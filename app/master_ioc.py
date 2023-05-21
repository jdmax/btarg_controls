from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from threading import Thread
import argparse
import importlib



async def main():
    '''
    Run IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    ioc, settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ":" + settings[ioc]['prefix']
    builder.SetDeviceName(device_name)

    p = DeviceIOC(device_name, settings[ioc], records)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

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
        self.pvs = {}

        self.device = self.module.Device(device_name, self.settings, self.pvs)

        for name, entry in self.pvs.items():
            if name in self.records:
                for field, value in self.records[name]['fields'].items():
                    setattr(self.pvs[name], field, value)   # set the attributes of the PV

        self.thread = IOCThread(self)
        self.thread.daemon = True
        self.thread.start()


class IOCThread(Thread):

    def __init__(self, parent):
        ''' Thread to regularly interact with device '''
        Thread.__init__(self)
        self.device = parent.device
        self.delay = parent.settings['delay']
        self.enable = parent.settings['enable']

        if self.enable:  # if not enabled, don't connect
            self.device.connect()

    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Identifies driver method to use from PV name. Delay time between measurements is in seconds.
        '''
        ticks = 2     # times per seconds to do device sets
        tocks = self.delay * ticks  # only run reads every tock
        i=0
        while True:
            sleep(1/ticks)
            i+=1
            if self.enable:
                self.device.do_sets()
                if i == tocks:
                    self.device.do_reads()
                    i = 0
                self.device.update_pvs()


def load_settings():
    '''Load device settings and records from YAML settings files. Argument parser allows '-s' to give a different folder'''

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--Settings", help = "Settings files folder")
    parser.add_argument("-i", "--IOC", help = "Name of IOC to start")
    args = parser.parse_args()
    folder = args.Settings if args.Settings else '..'

    with open(f'{folder}/settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/settings.yaml.")

    with open(f'{folder}/records.yaml') as f:  # Load settings from YAML files
        records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {folder}/records.yaml.")

    ioc_list = settings.keys()
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



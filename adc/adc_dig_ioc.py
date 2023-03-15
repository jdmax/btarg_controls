from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from threading import Thread
import random

from dat8148 import DAT8148


async def main():
    '''
    Run ADC IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':ADC'
    builder.SetDeviceName(device_name)

    p = ReadADC(device_name, settings['dat8148'], records)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class ReadADC:
    '''Set up PVs for Datexel ADC and connect to device
    '''

    def __init__(self, device_name, settings, records):
        '''
        Attributes:
            pvs: list of builder process variables created
        Arguments:
            settings: dict of device settings
            records: dict of record settings
        '''

        self.records = records
        self.settings = settings
        self.device_name = device_name
        self.Is = self.settings['indicators']  # Dict of Indicator names in channel order to associate PV with channel
        self.pvs = {}

        for pv_name in self.Is:  # Make PVs for all Is
            self.pvs[pv_name] = builder.boolIn(pv_name)
            for field, value in self.records[pv_name]['fields'].items():
                setattr(self.pvs[pv_name], field, value)   # set the attributes of the PV

        self.thread = DATThread(self)
        self.thread.setDaemon(True)
        self.thread.start()


class DATThread(Thread):

    def __init__(self, parent):
        ''' Thread reads every iteration, gets settings from parent.
        '''
        Thread.__init__(self)
        self.enable = parent.settings['enable']
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.Is = parent.Is
        self.values = [0] * len(self.Is)  # list of zeroes to start return Is
        if self.enable:  # if not enabled, don't connect
            self.t = DAT8148(parent.settings['ip'], parent.settings['port'],
                           parent.settings['timeout'])  # open connection to adc

    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Delay time between measurements is in seconds.
        '''
        while True:
            sleep(self.delay)

            if self.enable:
                self.values = self.t.read_all()
            else:
                self.values = [random.random() for l in self.values]  # return random number when we are not enabled
            for i, pv_name in enumerate(self.Is):
                out = True if self.values[i] else False
                self.pvs[pv_name].set(out)

def load_settings():
    '''Load device settings and records from YAML settings files. Argument parser allows '-s' to give a different folder'''

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--Settings", help = "Settings files folder")
    args = parser.parse_args()
    folder = args.Settings if args.Settings else '..'

    with open(f'{folder}/settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/settings.yaml.")

    with open(f'{folder}/records.yaml') as f:  # Load settings from YAML files
        records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {folder}/records.yaml.")

    return settings, records



if __name__ == "__main__":
    asyncio.run(main())
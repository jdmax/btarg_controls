from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from threading import Thread
import random

from ls218 import LS218


async def main():
    '''
    Run LS218 IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['ioc']['name'] + ':TEMP218'
    builder.SetDeviceName(device_name)

    p = ReadLS218(device_name, settings['lakeshore_218_1'], records['ls218_1'])
    q = ReadLS218(device_name, settings['lakeshore_218_2'], records['ls218_2'])

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class ReadLS218():
    '''Set up PVs for Lakeshore 218 and connect to device
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
        self.Is = self.records['Indicators']   # list of Indicator names in channel order to associate PV with channel
        self.pvs = {}
        
        for pv_name in self.Is:      # Make AIn PVs for all Is
            self.pvs[pv_name] = builder.aIn(pv_name)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):   # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)   # set the attributes of the PV        
                    
        self.thread = LS218Thread(self)
        self.thread.setDaemon(True)
        self.thread.start()


class LS218Thread(Thread):

    def __init__(self, parent):     
        ''' Thread reads every iteration, gets settings from parent. c_update is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.enable = parent.settings['enable'] 
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.Is = parent.Is
        self.values = [0]*len(self.Is)   # list of zeroes to start return Is
        if self.enable:                # if not enabled, don't connect
            self.t = LS218(parent.settings['ip'], parent.settings['port'], parent.settings['timeout'])     # open telnet connection to flow controllers

    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Delay time between measurements is in seconds.
        '''
        while True:
            sleep(self.delay)

            if self.enable:
                self.values = self.t.read_all()
            else:
                self.values = [random.random() for l in self.values]    # return random number when we are not enabled
            for i, pv_name in enumerate(self.Is):
                self.pvs[pv_name].set(self.values[i])


def load_settings():
    '''Load device settings and records from YAML settings file'''

    with open('../settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {'settings.yaml'}.")

    with open('../records.yaml') as f:  # Load settings from YAML files
        records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {'records.yaml'}.")

    return settings, records


if __name__ == "__main__":
    asyncio.run(main())
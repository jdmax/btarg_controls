from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from threading import Thread
import random

from ls336 import LS336


async def main():
    '''
    Run Lakeshore 336 IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':TEMP336'
    builder.SetDeviceName(device_name)

    p = LS336(device_name, settings['lakeshore_336'], records['ls336'])

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class ReadLS336():
    '''Set up PVs for Lakeshore 336 controller and connect to device
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
        self.Is = self.records['Indicators']  # list of Indicator names in channel order
        self.Cs = self.records['Controllers']  # list of Controller names in channel order
        self.Ms = self.records['Mults']  # list of Choice Menu names in channel order

        self.update = dict(zip(self.Cs + self.Ms, [False] * (len(self.Cs)+len(self.Ms))))  # dict with boolean to tell thread when to update
        self.pvs = {}

        for pv_name in self.Is:  # Make AIn PVs for all Is
            self.pvs[pv_name] = builder.aIn(pv_name)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):  # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)  # set the attributes of the PV

        for pv_name in self.Cs:  # Make AOut PVs for all Cs
            self.pvs[pv_name] = builder.aOut(pv_name, on_update_name=self.update_pv)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):  # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)  # set the attributes of the PV

        self.thread = LS336Thread(self)
        self.thread.setDaemon(True)
        self.thread.start()

    def update_pv(self, value, pv):
        '''When PV updated, let thread know
        '''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        self.update[pv_name] = True


class LS336Thread(Thread):

    def __init__(self, parent):
        ''' Thread reads every iteration, gets settings from parent. fc_update is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.enable = parent.settings['enable']
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.update = parent.update
        self.Is = parent.Is
        self.Cs = parent.Cs
        self.Ms = parent.Ms
        self.values = [0] * len(self.Is)  # list of zeroes to start return FIs
        self.setpoints = [0] * len(self.Cs)  # list of zeroes to start readback FCs
        self.mults = [0] * len(self.Ms)  # list of zeroes to start readback Multiple choice
        if self.enable:  # if not enabled, don't connect
            self.t = LS336(parent.settings['ip'], parent.settings['port'],
                          parent.settings['timeout'])  # open telnet connection to flow controllers

    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Delay time between measurements is in seconds.
        '''
        while True:
            sleep(self.delay)

            for pv_name, bool in self.update.items():
                if bool:  # there has been a change in this FC, update it
                    if self.enable:
                        self.t.set_setpoint(self.Cs.index(pv_name) + 1, self.pvs[pv_name].get())
                    else:
                        self.setpoints[self.Cs.index(pv_name)] = self.pvs[pv_name].get()  # for test, just echo back
                    self.update[pv_name] = False

            if self.enable:
                self.setpoints = self.t.read_setpoints()
                self.values = self.t.read_all()
            else:
                self.values = [random.random() for l in self.values]  # return random number when we are not enabled
            for i, pv_name in enumerate(self.Is):
                self.pvs[pv_name].set(self.values[i])
            for i, pv_name in enumerate(self.Cs):
                self.pvs[pv_name].set(self.setpoints[i])


def load_settings():
    '''Load device settings and records from YAML settings file'''

    with open('settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {'settings.yaml'}.")

    with open('records.yaml') as f:  # Load settings from YAML files
        records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {'records.yaml'}.")

    return settings, records


if __name__ == "__main__":
    asyncio.run(main())

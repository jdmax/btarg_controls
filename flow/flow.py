from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from threading import Thread
import random

from thcd import THCD


async def main():
    '''
    Run Flow IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':FLOW'
    builder.SetDeviceName(device_name)

    p = FlowControl(device_name, settings['flow_controller'], records['flow'])

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class FlowControl():
    '''Set up PVs for flow controller and connect to device
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
        self.Is = self.settings['indicators']  # list of Flow Indicator names in channel order
        self.Cs = self.settings['controllers']  # list of Flow Controller names in channel order
        self.update = dict(
            zip(self.Cs, [False] * len(self.Cs)))  # dict of FCs with boolean to tell thread when to update
        self.pvs = {}

        for pv_name in self.Is:  # Make AIn PVs for all FIs
            self.pvs[pv_name] = builder.aIn(pv_name)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):  # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)  # set the attributes of the PV

        for pv_name in self.Cs:  # Make AOut PVs for all FCs
            self.pvs[pv_name] = builder.aOut(pv_name, on_update_name=self.update_pv)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):  # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)  # set the attributes of the PV

        self.thread = FlowThread(self)
        self.thread.setDaemon(True)
        self.thread.start()

    def update_pv(self, value, pv):
        '''When PV updated, let thread know
        '''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        self.update[pv_name] = True


class FlowThread(Thread):

    def __init__(self, parent):
        ''' Thread reads every iteration, gets settings from parent. update is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.enable = parent.settings['enable']
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.update = parent.update
        self.Is = parent.Is
        self.Cs = parent.Cs
        self.values = [0] * len(self.Is)  # list of zeroes to start return FIs
        self.setpoints = [0] * len(self.Cs)  # list of zeroes to start readback FCs
        if self.enable:  # if not enabled, don't connect
            self.t = THCD(parent.settings['ip'], parent.settings['port'],
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

    with open('../settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from 'settings.yaml'.")

    with open('../records.yaml') as f:  # Load settings from YAML files
        records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from 'records.yaml'.")

    return settings, records


if __name__ == "__main__":
    asyncio.run(main())

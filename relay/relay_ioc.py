from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from threading import Thread
import argparse

from sr201 import SR201


async def main():
    '''
    Run relay IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':RLY'
    builder.SetDeviceName(device_name)

    p = RelayControl(device_name, settings['sr-201'], records)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class RelayControl():
    '''Set up PVs for relays and connect to device
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
        self.Cs = self.settings['controllers']  # list of Flow Controller names in channel order
        self.update = dict(
            zip(self.Cs, [False] * len(self.Cs)))  # dict of FCs with boolean to tell thread when to update
        self.pvs = {}

        for pv_name in self.Cs:  # Make boolOut PVs for all switches
            self.pvs[pv_name] = builder.boolOut(pv_name, on_update_name=self.update_pv)
            for field, value in self.records[pv_name]['fields'].items():
                setattr(self.pvs[pv_name], field, value)   # set the attributes of the PV

        self.thread = RelayThread(self)
        self.thread.setDaemon(True)
        self.thread.start()

    def update_pv(self, value, pv):
        '''When PV updated, let thread know
        '''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        self.update[pv_name] = True


class RelayThread(Thread):

    def __init__(self, parent):
        ''' Thread reads every iteration, gets settings from parent. update is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.enable = parent.settings['enable']
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.update = parent.update
        self.Cs = parent.Cs
        self.states = [0] * len(self.Cs)  # list of zeroes to start readback Cs
        if self.enable:  # if not enabled, don't connect
            self.t = SR201(parent.settings['ip'], parent.settings['port'],
                          parent.settings['timeout'])  # open telnet connection to flow controllers

    def run(self):
        '''
        Thread to write PVS to switch channels. Delay time between measurements is in seconds.
        '''
        while True:
            sleep(self.delay)

            for pv_name, bool in self.update.items():
                if bool:  # there has been a change in this FC, update it
                    if self.enable:
                        self.states = self.t.switch(self.pvs[pv_name].get(), str(self.Cs.index(pv_name) + 1))
                    else:
                        self.states[self.Cs.index(pv_name)] = self.pvs[pv_name].get()  # for test, just echo back
                    self.update[pv_name] = False

            try:
                for i, pv_name in enumerate(self.Cs):    # set the PV to the value returned to be sure we switched
                    if self.states[i]==1:
                        self.pvs[pv_name].set(True)
                    else:
                        self.pvs[pv_name].set(False)
            except Exception as e:
                print(f"PV set failed: {e}")


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

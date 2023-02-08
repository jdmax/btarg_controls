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
        self.channels = self.records['Channels']  # ordered list of 336 channels dicts
        self.update_flags = {}     # build update flag dict from records
        for channel in self.channels:
            for pv_name in channel['Controllers']:
                self.update_flags[pv_name] = False
            for pv_name in channel['Mults']:
                self.update_flags[pv_name] = False
        self.pvs = {}

        for channel in self.channels:
            for pv_name in channel['Indicators']:  # Make AIn PVs for all Is
                self.pvs[pv_name] = builder.aIn(pv_name)
                for field, value in self.records[pv_name].items():
                    if not isinstance(value, dict):  # don't do the dicts of states
                        setattr(self.pvs[pv_name], field, value)  # set the attributes of the PV

            for pv_name in channel['Controllers']:  # Make AOut PVs for all Cs
                self.pvs[pv_name] = builder.aOut(pv_name, on_update_name=self.update)
                for field, value in self.records[pv_name].items():
                    if not isinstance(value, dict):  # don't do the lists of states
                        setattr(self.pvs[pv_name], field, value)  # set the attributes of the PV

            for pv_name, list in channel['Mults']:  # Make mbbOut PVs for all Ms
                self.pvs[pv_name] = builder.mbbOut(pv_name, *list, on_update_name=self.update)
                for field, value in self.records[pv_name].items():
                    if not isinstance(value, dict):  # don't do the lists of states
                        setattr(self.pvs[pv_name], field, value)  # set the attributes of the PV

        self.thread = LS336Thread(self)
        self.thread.setDaemon(True)
        self.thread.start()

    def update(self, value, pv):
        '''When PV updated, let thread know
        '''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        self.update_flags[pv_name] = True


class LS336Thread(Thread):

    def __init__(self, parent):
        ''' Thread reads every iteration, gets settings from parent. update_pv is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.enable = parent.settings['enable']
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.update_flags = parent.update_flags
        self.channels = parent.channels
        self.temps = [0] * len(self.channels)  # list of zeroes to start return Is
        self.heats = [0] * len(self.channels)
        if self.enable:  # if not enabled, don't connect
            self.t = LS336(parent.settings['ip'], parent.settings['port'],
                          parent.settings['timeout'])  # open telnet connection

    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Identifies driver method to use from PV name. Delay time between measurements is in seconds.
        '''
        while True:
            sleep(self.delay)
            chan = 0               # device channel of the current PV
            for pv_name, bool in self.update_flags.items():
                if bool:  # there has been a change in this FC, update it
                    p = pv_name[:-2]  # pv_name without kP, kI or kD
                    for i, channel in self.channels.enumerate():  # determine what channel we are on
                        if pv_name in channel['Controllers']:
                            chan = i + 1
                        elif pv_name in channel['Mults']:
                            chan = i + 1
                    # figure out what type of PV this is, and send it to the right method
                    if 'kP' in pv_name or 'kI' in pv_name or 'kD' in pv_name: # is this a PID control record?
                        if self.enable:
                            dict = {}
                            k_list = ['kP','kI','kD']
                            for k in k_list:
                                dict[k] = self.pvs[p+k].get()               # read pvs to send to device
                            values = self.t.set_pid(chan, dict['kP'], dict['kI'], dict['kD'])
                            [self.pvs[p+k].set(values[i]) for i, k in enumerate(k_list)]   # set values read back
                    elif 'SP' in pv_name:   # is this a setpoint?
                        if self.enable:
                            value = self.t.set_setpoint(chan, self.pvs[pv_name].get())
                            self.pvs[pv_name].set(value)   # set returned value
                    elif 'Mode' in pv_name:
                        if self.enable:
                            value = self.t.set_outmode(chan, self.pvs[pv_name].get(), chan, 0)
                            self.pvs[pv_name].set(value)   # set returned value
                    elif 'Range' in pv_name:
                        if self.enable:
                            value = self.t.set_range(chan, self.pvs[pv_name].get())
                            self.pvs[pv_name].set(value)   # set returned value
                    else:
                        print('Error, control PV not categorized.')
                    self.update_flags[pv_name] = False

            if self.enable:
                self.temps = self.t.read_temps()
                self.heats[0] = self.t.read_heater(1)
                self.heats[1] = self.t.read_heater(2)
            else:
                self.temps = [random.random() for l in self.temps]  # return random number when we are not enabled
                self.heats = [random.random()]*2  # return random number when we are not enabled

            for i, channel in enumerate(self.channels):
                for pv_name in channel['Indicators']: # find the indicator PV and set from reading
                    if '_TI' in pv_name:
                        self.pvs[pv_name].set(self.temps[i])
                    if '_Heater' in pv_name:
                        self.pvs[pv_name].set(self.heats[i])


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

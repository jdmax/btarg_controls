from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from threading import Thread
import random
import argparse

from dp832 import DP832


async def main():
    '''
    Run Rigol DP832 IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':LL'
    builder.SetDeviceName(device_name)

    p = ReadDP832(device_name, settings['rigol_dp832'], records)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class ReadDP832():
    '''Set up PVs for Rigol DP832 power supply and connect to device
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
        self.channels = self.settings['channels']  # ordered list of channels
        self.update_flags = {}     # build update flag dict from records
        self.pvs = {}

        for channel in self.channels:    # set up PVs for each channel
            if 'None' in channel: continue
            self.pvs[channel+"_VI"] = builder.aIn(channel+"_VI")   # Voltage
            self.pvs[channel+"_CI"] = builder.aIn(channel+"_CI")   # Current

            self.pvs[channel + "_CC"] = builder.aOut(channel + "_CC", on_update_name=self.update)

            self.pvs[channel + "_Mode"] = builder.boolOut(channel + "_Mode", on_update_name=self.update)

        for name, entry in self.pvs.items():
            if name in self.records:
                for field, value in self.records[name]['fields'].items():
                    setattr(self.pvs[name], field, value)   # set the attributes of the PV

        self.thread = DP832Thread(self)
        self.thread.daemon = True
        self.thread.start()

    def update(self, value, pv):
        '''When PV updated, let thread know
        '''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        self.update_flags[pv_name] = True


class DP832Thread(Thread):

    def __init__(self, parent):
        ''' Thread reads every iteration, gets settings from parent. update_pv is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.settings = parent.settings
        self.enable = parent.settings['enable']
        self.delay = parent.settings['delay']
        self.volt_lim = parent.settings['voltage_limit']
        self.pvs = parent.pvs
        self.update_flags = parent.update_flags
        self.channels = parent.channels
        self.volt_sets = [0] * len(self.channels)  # list of zeroes to start
        self.current_sets = [0] * len(self.channels)  # list of zeroes to start
        self.volt_outs = [0] * len(self.channels)  # list of zeroes to start
        self.current_outs = [0] * len(self.channels)  # list of zeroes to start
        self.states = [False] * len(self.channels)  # list of False to start
        if self.enable:  # if not enabled, don't connect
            self.t = DP832(self.settings['ip'], self.settings['port'],
                           self.settings['timeout'])  # open telnet connection
    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Identifies driver method to use from PV name. Delay time between measurements is in seconds.
        '''
        while True:
            sleep(self.delay)
            for pv_name, bool in self.update_flags.items():
                if bool and self.enable:  # there has been a change, update it
                    print(pv_name)
                    p = pv_name.split("_")[0]   # pv_name root
                    chan = self.channels.index(p) + 1  # determine what channel we are on
                    # figure out what type of PV this is, and send it to the right method
                    if 'CC' in pv_name:   # is this a current set? Voltage set from settings file
                        value = self.t.set(chan, self.volt_lim, self.pvs[pv_name].get())
                        self.pvs[pv_name].set(value)   # set returned current
                    elif 'Mode' in pv_name:
                        value = self.t.set_state(chan, self.pvs[pv_name].get())
                        self.pvs[pv_name].set(int(value))   # set returned value
                    else:
                        print('Error, control PV not categorized.', pv_name)
                    self.update_flags[pv_name] = False

            if self.enable:    # read all values from DP832
                for i, channel in enumerate(self.channels):
                    if 'None' in channel: continue
                    try:
                        self.volt_outs[i], self.current_outs[i], power = self.t.read(i+1)
                        self.volt_sets[i], self.current_sets[i] = self.t.read_sp(i+1)
                        self.states[i] = self.t.read_state(i+1)
                    except OSError:
                        self.reconnect()
            else:
                self.volt_outs = [random.random() for l in self.channels]  # return random number when we are not enabled

            try:   # set new values to PVs
                for i, channel in enumerate(self.channels):
                    if 'None' in channel: continue
                    self.pvs[channel+'_VI'].set(self.volt_outs[i])
                    self.pvs[channel+'_CI'].set(self.current_outs[i])
                    self.pvs[channel+'_CC'].set(self.current_sets[i])
                    self.pvs[channel+'_Mode'].set(self.states[i])

            except OSError:
                self.reconnect()
            except Exception as e:
                print(f"PV set failed: {e}", channel)

    def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        try:
            self.t = DP832(self.settings['ip'], self.settings['port'],
                           self.settings['timeout'])  # open telnet connection
        except Exception as e:
            print("Failed reconnect", e)


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

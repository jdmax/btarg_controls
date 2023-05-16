from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from datetime import datetime
from threading import Thread
import random
import argparse

from thcd import THCD, THCDserial


async def main():
    '''
    Run Flow IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':FLOW'
    builder.SetDeviceName(device_name)

    p = FlowControl(device_name, settings['flow_controller'], records)

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
        self.channels = self.settings['channels']  # ordered list of channels
        self.update_flags = {}     # build update flag dict from records
        self.pvs = {}

        mode_list = [['Auto', 0], [ 'Open', 1 ], [ 'Closed', 2 ]]

        for channel in self.channels:    # set up PVs for each channel
            if "_FI" in channel:
                self.pvs[channel] = builder.aIn(channel)
            elif "None" in channel:
                pass
            else:
                self.pvs[channel+"_FI"] = builder.aIn(channel+"_FI")
                self.pvs[channel+"_FC"] = builder.aOut(channel+"_FC", on_update_name=self.update)
                self.pvs[channel+"_Mode"] = builder.mbbOut(channel+"_Mode", *mode_list, on_update_name=self.update)

        for name, entry in self.pvs.items():
            if name in self.records:
                for field, value in self.records[name]['fields'].items():
                    setattr(self.pvs[name], field, value)   # set the attributes of the PV

        self.thread = FlowThread(self)
        self.thread.daemon = True
        self.thread.start()

    def update(self, value, pv):
        '''When PV updated, let thread know
        '''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        self.update_flags[pv_name] = True


class FlowThread(Thread):

    def __init__(self, parent):
        ''' Thread reads every iteration, gets settings from parent. update is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.settings = parent.settings
        self.enable = parent.settings['enable']
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.update_flags = parent.update_flags
        self.channels = parent.channels
        self.values = [0] * len(self.channels)  # list of zeroes to start return FIs
        self.setpoints = [0] * len(self.channels)  # list of zeroes to start readback FCs
        self.outmodes = [0] * len(self.channels)  # list of zeroes to start readback modes
        if self.enable:  # if not enabled, don't connect
            #self.t = THCD(parent.settings['ip'], parent.settings['port'],
                          #parent.settings['timeout'])
            self.t = THCDserial()  # open serial connection to flow controllers

    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Delay time between measurements is in seconds.
        '''
        now = datetime.now()
        while True:
            sleep(self.delay)

            for pv_name, bool in self.update_flags.items():
                if bool and self.enable:  # there has been a change in this controller, update it
                    if '_FC' in pv_name:
                        try:
                            self.t.set_setpoint(self.channels.index(pv_name) + 1, self.pvs[pv_name].get())
                            sleep(0.1)
                        except OSError:
                            self.reconnect()
                    elif '_Mode' in pv_name:
                        try:
                            self.t.set_mode(self.channels.index(pv_name) + 1, self.pvs[pv_name].get())
                            sleep(0.1)
                        except OSError:
                            self.reconnect()
                    self.update[pv_name] = False

            if self.enable:
                try:   # Do reads from device, with short delays between
                    self.setpoints = self.t.read_setpoints()
                    sleep(0.1)
                    self.values = self.t.read_all()
                    sleep(0.1)
                    self.outmodes = self.t.read_modes()
                except OSError:
                    self.reconnect()
            else:
                self.values = [random.random() for l in self.values]  # return random number when we are not enabled
            try:
                for i, channel in enumerate(self.channels):
                    if "_FI" in channel:
                        self.pvs[channel].set(self.values[i])
                    elif "None" in channel:
                        pass
                    else:
                        self.pvs[channel + "_FI"].set(self.values[i])
                        self.pvs[channel + "_FC"].set(self.setpoints[i])
                        self.pvs[channel + "_Mode"].set(self.outmodes[i])
            except Exception as e:
                print(f"PV set failed: {e}")

            diff = datetime.now() - now
            if diff.total_seconds() > 150:    # trying fix to THCD falling off network
                print(diff)
                self.reconnect()
                now = datetime.now()

    def reconnect(self):
        del self.t
        sleep(1)
        print("Attempting reconnect.")
        try:
            self.t = THCDserial()  # open serial connection to flow controllers
            #self.t = THCDserial(self.settings['ip'], self.settings['port'],
            #               self.settings['timeout'])  # reopen telnet connection
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

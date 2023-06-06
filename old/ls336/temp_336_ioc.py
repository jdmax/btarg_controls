from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
from time import sleep
from threading import Thread
import argparse

from devices.ls336 import LS336


async def main():
    '''
    Run Lakeshore 336 IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':TEMP'
    builder.SetDeviceName(device_name)

    p = ReadLS336(device_name, settings['lakeshore_336'], records)

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
        self.channels = self.settings['channels']  # ordered list of 336 channels
        self.update_flags = {}     # build update flag dict from records
        self.pvs = {}

        mode_list = [['Off', 0], [ 'Closed Loop', 1 ], [ 'Zone', 2 ], [ 'Open Loop', 3 ]]
        range_list = [['Off', 0], [ 'Low', 1 ], [ 'Med', 2 ], [ 'High', 3 ]]

        for channel in self.channels:    # set up PVs for each channel
            if "_TI" in channel:
                self.pvs[channel] = builder.aIn(channel)
            elif "None" in channel:
                pass
            else:
                self.pvs[channel+"_TI"] = builder.aIn(channel+"_TI")
                self.pvs[channel+"_Heater"] = builder.aIn(channel+"_Heater")

                self.pvs[channel+"_Manual"] = builder.aOut(channel+"_Manual", on_update_name=self.update)
                self.pvs[channel+"_kP"] = builder.aOut(channel+"_kP", on_update_name=self.update)
                self.pvs[channel+"_kI"] = builder.aOut(channel+"_kI", on_update_name=self.update)
                self.pvs[channel+"_kD"] = builder.aOut(channel+"_kD", on_update_name=self.update)
                self.pvs[channel+"_SP"] = builder.aOut(channel+"_SP", on_update_name=self.update)

                self.pvs[channel+"_Mode"] = builder.mbbOut(channel+"_Mode", *mode_list, on_update_name=self.update)
                self.pvs[channel+"_Range"] = builder.mbbOut(channel+"_Range", *range_list, on_update_name=self.update)

        for name, entry in self.pvs.items():
            if name in self.records:
                for field, value in self.records[name]['fields'].items():
                    setattr(self.pvs[name], field, value)   # set the attributes of the PV

        self.thread = LS336Thread(self)
        self.thread.daemon = True
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
        self.settings = parent.settings
        self.enable = parent.settings['enable']
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.update_flags = parent.update_flags
        self.channels = parent.channels
        self.temps = [0] * len(self.channels)  # list of zeroes to start
        self.num_full = 0    # number of channels with full heater controls
        for chan in self.channels:
            if "_TI" in chan or "None" in chan:
                pass
            else:
                self.num_full += 1
        self.heats = [0] * self.num_full
        self.pids = [0] * self.num_full
        self.outmodes = [0] * self.num_full
        self.ranges = [0] * self.num_full
        self.sps = [0] * self.num_full
        self.manuals = [0] * self.num_full
        if self.enable:  # if not enabled, don't connect
            self.t = LS336(self.settings['ip'], self.settings['port'],
                           self.settings['timeout'])  # open telnet connection
    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Identifies driver method to use from PV name. Delay time between measurements is in seconds.
        '''
        ticks = 2     # times per seconds to do device sets
        tocks = self.delay * tick  # only run reads every tock
        i=0
        while True:
            sleep(1/ticks)
            i+=1
            if self.enable:
                self.do_sets()
                if i == tocks:
                    self.do_reads()
                    i = 0
                self.update_pvs()

    def do_sets(self):
        '''If PV has changed, find the correct method to set it on the device'''
        for pv_name, bool in self.update_flags.items():
            if bool and self.enable:  # there has been a change, update it
                p = pv_name.split("_")[0]   # pv_name root
                chan = self.channels.index(p) + 1  # determine what channel we are on
                # figure out what type of PV this is, and send it to the right method
                if 'kP' in pv_name or 'kI' in pv_name or 'kD' in pv_name: # is this a PID control record?
                    dict = {}
                    k_list = ['kP','kI','kD']
                    for k in k_list:
                        dict[k] = self.pvs[p+"_"+k].get()               # read pvs to send to device
                    values = self.t.set_pid(chan, dict['kP'], dict['kI'], dict['kD'])
                    [self.pvs[p+"_"+k].set(values[i]) for i, k in enumerate(k_list)]   # set values read back
                elif 'SP' in pv_name:   # is this a setpoint?
                    value = self.t.set_setpoint(chan, self.pvs[pv_name].get())
                    self.pvs[pv_name].set(value)   # set returned value
                elif 'Manual' in pv_name:  # is this a manual out?
                    value = self.t.set_man_heater(chan, self.pvs[pv_name].get())
                    self.pvs[pv_name].set(value)  # set returned value
                elif 'Mode' in pv_name:
                    value = self.t.set_outmode(chan, self.pvs[pv_name].get(), chan, 0)
                    self.pvs[pv_name].set(int(value))   # set returned value
                elif 'Range' in pv_name:
                    value = self.t.set_range(chan, self.pvs[pv_name].get())
                    self.pvs[pv_name].set(int(value))   # set returned value
                else:
                    print('Error, control PV not categorized.')
                self.update_flags[pv_name] = False

    def do_reads(self):
        '''Match variables to methods in device driver'''
        try:
            self.temps = self.t.read_temps()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.heats[i] = self.t.read_heater(i+1)
                self.pids[i] = self.t.read_pid(i+1)
                self.outmodes[i] = self.t.read_outmode(i+1)
                self.ranges[i] = self.t.read_range(i+1)
                self.sps[i] = self.t.read_setpoint(i+1)
                self.manuals[i] = self.t.read_man_heater(i+1)
        except OSError:
            self.reconnect()
        return

    def update_pvs(self):
        '''Set new values from the reads to the PVs'''
        try:
            for i, channel in enumerate(self.channels):
                if "_TI" in channel:
                    self.pvs[channel].set(self.temps[i])
                elif "None" in channel:
                    pass
                else:
                    self.pvs[channel + '_TI'].set(self.temps[i])
                    self.pvs[channel + '_Heater'].set(self.heats[i])
                    self.pvs[channel + '_kP'].set(self.pids[i][0])
                    self.pvs[channel + '_kI'].set(self.pids[i][1])
                    self.pvs[channel + '_kD'].set(self.pids[i][2])
                    self.pvs[channel + '_Mode'].set(int(self.outmodes[i]))
                    self.pvs[channel + '_Range'].set(int(self.ranges[i]))
                    self.pvs[channel + '_SP'].set(self.sps[i])
                    self.pvs[channel + '_Manual'].set(self.manuals[i])
        except OSError:
            self.reconnect()
        except Exception as e:
            print(f"PV set failed: {e}", channel)


    def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        try:
            self.t = LS336(self.settings['ip'], self.settings['port'],
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

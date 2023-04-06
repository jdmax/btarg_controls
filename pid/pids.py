from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
import epics
from simple_pid import PID
from threading import Thread
from time import sleep
import numpy as np
import argparse
import os



async def main():
    '''
    Run PID IOC: load settings, create dispatcher, set name, start loops, do IOC boilerplate
    '''
    print('TGT:BTARG:PID:Test_Power', epics.caget('TGT:BTARG:PID:Test_Power'))
    pids = {}
    settings, pid_settings = load_settings()
    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':PID'
    builder.SetDeviceName(device_name)

    for pid_name, pdict in pid_settings.items():
        pids[pid_name] = PIDLoop(device_name, pid_name, pdict)
        pids[pid_name].start()  # start thread to monitor pid

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class PIDLoop(Thread):
    '''Instantiates a PID loop and thread, makes PVs
    '''
    
    def __init__(self, device_name, pid_name, pdict):
        Thread.__init__(self)
        self.device_name = device_name
        self.pvs = {}   # dict of PVs for this PID
        self.pid_name = pid_name
        self.in_pv = pdict['input']
        self.out_pv = pdict['output']
        self.update = dict(zip(pdict['outs'].keys(),[False]*len(pdict['outs'].keys())))   # True to update pv with the key as name
        
        for out, value in pdict['outs'].items():   # make and set pvs with values from settings
            pv_name = pid_name+'_'+out      # PV names start with PID name
            if isinstance(value, bool):             # setup PVs as boolean or analog
                self.pvs[pv_name] = builder.boolOut(pv_name, on_update_name = self.update_attr)
            else:
                self.pvs[pv_name] = builder.aOut(pv_name, on_update_name = self.update_attr)
            self.pvs[pv_name].set(value)  # put this is try statement to catch errors from epics
        
        self.pid = PID()    # set up simple_pid 
        for out in pdict['outs'].keys():   # set all parameters to pid object except the max and min change
            if not 'change' in out:
                setattr(self.pid, out, self.pvs[pid_name+'_'+out].get())
        try:
            print(epics.cainfo(self.out_pv), self.out_pv)
            high = epics.caget(self.out_pv + '.DRVH')
            low = epics.caget(self.out_pv + '.DRVL')  # put this is try statement to catch errors from epics
            self.pid.output_limits = (low, high)  # set limits based on drive limits from output PV
        except Exception as e:
            print(e)
        self.delay = self.pvs[pid_name+'_'+'sample_time'].get()
        self.max_change = self.pvs[self.pid_name+'_'+'max_change'].get()
        self.min_change = self.pvs[self.pid_name+'_'+'min_change'].get()

    def update_attr(self, value, pv):
        '''
        PV value has changed for one of the pid attributes, update PIDLoop
        '''
        pv_name = pv.replace(self.device_name+':'+self.pid_name, '')   # remove device name from PV to get bare out pv name
        self.update[pv_name] = True
            
    def run(self):    
        print('Started thread for', self.pid_name)
        
        while True:
            sleep(self.delay)
            for pv_name, b in self.update.items():
                if b:   # there has been a change in this out pv, update it in the pid
                    if 'auto_mode' in pv_name:
                        self.pid.set_auto_mode( 
                            self.pvs[self.pid_name+'_auto_mode'].get(),
                            last_output = caget(self.out_pv)
                        )   # if turning on, start at previous output value
                    if 'change' in pv_name:
                        self.min_change = self.pvs[self.pid_name+'_min_change'].get()
                        self.max_change = self.pvs[self.pid_name+'_max_change'].get()
                    if 'sample_time' in pv_name:
                        self.delay = self.pvs[self.pid_name+'_'+pv_name].get()
                        setattr(self.pid, pv_name, self.pvs[self.pid_name+'_'+pv_name].get())
                    else:    
                        setattr(self.pid, pv_name, self.pvs[self.pid_name+'_'+pv_name].get())

            last_output = self.pid._last_output
            input = epics.caget(self.in_pv)
            output = self.pid(input)
            
            if abs(last_output - output) > self.max_change:   # check max and min change and alter output if needed
                output = output + self.max_change * np.sign(last_output - output)
                self.pid._last_output = output
            elif abs(last_output - output) < self.min_change:                
                output = last_output
                self.pid._last_output = output           
            
            # write output to out PV
            epics.caput(self.out_pv)


def load_settings():
    '''Load pid settings and records from YAML settings files. Argument parser allows '-s' to give a different folder'''

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--Settings", help = "Settings files folder")
    args = parser.parse_args()
    folder = args.Settings if args.Settings else '..'   # default is directory above

    with open(f'{folder}/settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/settings.yaml.")

    with open(f'{folder}/pids.yaml') as f:  # Load settings from YAML files
        pids = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/pids.yaml.")

    return settings, pids


if __name__ == "__main__":
    asyncio.run(main())
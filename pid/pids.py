from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
import aioca
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

    pids = {}
    runs = []
    settings, pid_settings = load_settings()
    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    loop = asyncio.get_event_loop()
    device_name = settings['prefix'] + ':PID'
    builder.SetDeviceName(device_name)

    for pid_name, pdict in pid_settings.items():
        pids[pid_name] = PIDLoop(device_name, pid_name, pdict)
        await pids[pid_name].pid_setup()    # wait to get pids set up
        task = loop.create_task(pids[pid_name].run_pid())  # Run all pids concurrently

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)
    await task
    softioc.interactive_ioc(globals())

class PIDLoop():
    '''Instantiates a PID loop and thread, makes PVs
    '''
    
    def __init__(self, device_name, pid_name, pdict):
        self.device_name = device_name
        self.pvs = {}   # dict of PVs for this PID
        self.pid_name = pid_name
        self.in_pv = pdict['input']
        self.out_pv = pdict['output']
        self.outs = pdict['outs']
        self.update = dict(zip(self.outs.keys(), [False]*len(self.outs.keys())))   # True to update pv with the key as name
        
        for out, value in pdict['outs'].items():   # make and set pvs with values from settings
            pv_name = pid_name+'_'+out      # PV names start with PID name
            if isinstance(value, bool):             # setup PVs as boolean or analog
                self.pvs[pv_name] = builder.boolOut(pv_name, on_update_name = self.update_attr)
            else:
                self.pvs[pv_name] = builder.aOut(pv_name, on_update_name = self.update_attr)
            self.pvs[pv_name].set(value)  # put this in try statement to catch errors from epics


    async def pid_setup(self):
        self.pid = PID()    # set up simple_pid 
        for out in self.outs.keys():   # set all parameters to pid object except the max and min change
            if not 'change' in out:
                setattr(self.pid, out, self.pvs[self.pid_name+'_'+out].get())
        try:
            high = await aioca.caget(self.out_pv + '.DRVH')
            low = await aioca.caget(self.out_pv + '.DRVL')  # put this is try statement to catch errors from epics
            self.pid.output_limits = (low, high)  # set limits based on drive limits from output PV
        except Exception as e:
            print(e)
        self.delay = self.pvs[self.pid_name+'_'+'sample_time'].get()
        self.max_change = self.pvs[self.pid_name+'_'+'max_change'].get()
        self.min_change = self.pvs[self.pid_name+'_'+'min_change'].get()
        self.last_output = await aioca.caget(self.out_pv)
        print('PID setup', self.pid_name, self.last_output)

    def update_attr(self, value, pv):
        '''
        PV value has changed for one of the pid attributes, update PIDLoop
        '''
        pv_name = pv.replace(self.device_name+':'+self.pid_name+'_', '')   # remove device and pid name from PV to get bare out name
        self.update[pv_name] = True

    async def run_pid(self):
        print('test')
        while True:
            await asyncio.sleep(self.delay)
            print('Run loop iteration')
            for pv_name, b in self.update.items():
                if b:   # there has been a change in this out pv, update it in the pid
                    print(pv_name, b)
                    if 'auto_mode' in pv_name:
                        self.last_output = await aioca.caget(self.out_pv)
                        print('last', self.last_output)
                        self.pid.set_auto_mode( 
                            self.pvs[self.pid_name+'_auto_mode'].get(),
                            last_output = self.last_output
                        )   # if turning on, start at previous output value
                    if 'change' in pv_name:
                        self.min_change = self.pvs[self.pid_name+'_min_change'].get()
                        self.max_change = self.pvs[self.pid_name+'_max_change'].get()
                    if 'sample_time' in pv_name:
                        self.delay = self.pvs[self.pid_name+'_'+pv_name].get()
                        setattr(self.pid, pv_name, self.pvs[self.pid_name+'_'+pv_name].get())
                    else:    
                        setattr(self.pid, pv_name, self.pvs[self.pid_name+'_'+pv_name].get())

            if self.pid._last_output:
                self.last_output = self.pid._last_output
            input = await aioca.caget(self.in_pv)
            output = self.pid(input)
            print(self.last_output, output, input)
            if self.pid.auto_mode:
                if abs(self.last_output - output) > self.max_change:   # check max and min change and alter output if needed
                    output = output + self.max_change * np.sign(self.last_output - output)
                    self.pid._last_output = output
                elif abs(self.last_output - output) < self.min_change:
                    output = self.last_output
                    self.pid._last_output = output
                await aioca.caput(self.out_pv, output) # write output to out PV


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
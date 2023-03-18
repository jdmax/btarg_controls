from softioc.builder import aOut, boolOut
from epics import caget
from simple_pid import PID
from collections import ChainMap
from threading import Thread
from time import sleep
import numpy as np
import argparse


class PIDSetup():
    '''Class to setup PID loops from entries in yaml file. Makes pids and threads to run them.
    '''
    def __init__(self, parent, pids):
        '''Takes pids, a dictionary from config file
        '''
        self.pids = {}
        self.pid_settings = load_settings()
        for pid_name, pdict in self.pid_settings.items():
            self.pids[pid_name] = PIDLoop(pid_name, pdict)
            self.pids[pid_name].start()    # start thread to monitor pid
            
        #self.pvs = ChainMap([p.pvs for p in self.pids.values()])   # combine all the PID PVS
    
class PIDLoop(Thread):
    '''Instantiates a PID loop and thread, makes PVs
    '''
    
    def __init__(self, pid_name, pdict):
        Thread.__init__(self)
        self.pvs = {}   # dict of PVs for this PID
        self.pid_name = pid_name
        self.in_pv = pdict['input']
        self.out_pv = pdict['output']
        self.update = dict(zip(pdict['outs'].keys(),[False]*len(pdict['outs'].keys())))   # True to update pv with the key as name
        
        for out, value in pdict['outs'].items():   # make and set pvs with values from settings
            pv_name = pid_name+'_'+out      # PV names start with PID name
            if isinstance(value, bool):             # setup PVs as boolean or analog
                self.pvs[pv_name] = boolOut(pv_name, on_update_name = self.update_attr)
            else:
                self.pvs[pv_name] = aOut(pv_name, on_update_name = self.update_attr)
            self.pvs[pv_name].set('value', value)
        
        self.pid = PID()    # set up simple_pid 
        for out in pdict['outs'].keys():   # set all parameters to pid object except the max and min change
            if not 'change' in out:
                setattr(self.pid, out, self.pvs[pid_name+'_'+out].get())
        low = caget(self.out_pv+'DRVL')
        high = caget(self.out_pv+'DRVH')
        self.pid.output_limits = (low, high)  # set limits based on drive limits from output PV
        self.delay = self.pvs[pid_name+'_'+'sample_time'].get()
        self.max_change = self.pvs[self.pid_name+'_'+'max_change'].get()
        self.min_change = self.pvs[self.pid_name+'_'+'min_change'].get()
            
    def run(self):    
        print('Started thread for', self.pid_name)
        
        while True:
            sleep(self.delay)
            for pv_name, bool in self.update.items():
                if bool:   # there has been a change in this out pv, update it in the pid
                    if 'auto_mode' in pv_name:
                        self.pid.set_auto_mode( 
                            self.pvs[self.pid_name+'_auto_mode'].get(),
                            last_output = self.out_pv.get()
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
            input = self.in_pv.get()
            output = self.pid(input)
            
            if abs(last_output - output) > self.max_change:   # check max and min change and alter output if needed
                output = output + self.max_change * np.sign(last_output - output)
                self.pid._last_output = output
            elif abs(last_output - output) < self.min_change:                
                output = last_output
                self.pid._last_output = output           
            
            # write output to out PV
            self.out_pv.set(output)
    
    def update_attr(value, out):
        '''
        PV value has changed for one of the pid atttributes, update PIDLoop
        '''
        pv_name = pv.replace(self.device_name+':'+self.pid_name, '')   # remove device name from PV to get bare out pv name
        self.update[pv_name] = True

def load_settings():
    '''Load pid settings and records from YAML settings files. Argument parser allows '-s' to give a different folder'''

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--Settings", help = "Settings files folder")
    args = parser.parse_args()
    folder = args.Settings if args.Settings else '..'   # default is directory above

    with open(f'{folder}/pids.yaml') as f:  # Load settings from YAML files
        pids = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/pids.yaml.")
    return pids
from softioc.builder import aIn, aOut
from time import sleep
from threading import Thread
import random

from app.ls218 import LS218

class ReadLS218():
    '''Set up PVs for Lakeshore 218 and connect to device
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
        self.device_name = device_names
        self.Is = self.records['Indictors']   # list of Flow Indicator names in channel order 
        self.pvs = {}
        
        for pv_name in self.Is:      # Make AIn PVs for all FIs
            self.pvs[pv_name] = aIn(pv_name)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):   # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)   # set the attributes of the PV        
                    
        self.thread = FlowThread(self)  
        self.thread.setDaemon(True)
        self.thread.start()
        
class LS218Thread(Thread):

    def __init__(self, parent):     
        ''' Thread reads every iteration, gets settings from parent. fc_update is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.enable = parent.settings['enable'] 
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.Is = parent.Is
        self.Cs = parent.Cs
        self.values = [0]*len(self.Is)   # list of zeroes to start return FIs
        self.setpoints = [0]*len(self.Cs)   # list of zeroes to start readback FCs
        if self.enable:                # if not enabled, don't connect
            self.t = THCD(parent.settings['ip'], parent.settings['port'], parent.settings['timeout'])     # open telnet connection to flow controllers

    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Delay time between measurements is in seconds.
        '''
        while True:
            sleep(self.delay)
            
            for pv_name, bool in self.fc_update.items():
                if bool:   # there has been a change in this FC, update it
                    if self.enable:
                        self.t.set_setpoint(self.Cs.index(pv_name)+1, self.pvs[pv_name].get())
                    else:
                        self.setpoints[self.Cs.index(pv_name)] = self.pvs[pv_name].get()   # for test, just echo back
                    self.fc_update[pv_name] = False  
                
            if self.enable:
                self.setpoints = self.t.read_setpoints()   
                self.values = self.t.read_all()
            else:
                self.values = [random.random() for l in self.values]    # return random number when we are not enabled
            for i, pv_name in enumerate(self.Is):
                self.pvs[pv_name].set(self.values[i])                
            for i, pv_name in enumerate(self.Cs):
                self.pvs[pv_name].set(self.setpoints[i])    

  
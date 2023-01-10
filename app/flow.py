from softioc.builder import aIn, aOut
from time import sleep
from threading import Thread
import random

from app.thcd import THCD

class FlowControl():
    '''Set up PVs for flow controller and connect to device
    '''
    
    def __init__(self, settings, records):
        '''
        Attributes:
            pvs: list of builder process variables created 
        Arguments:
            settings: dict of device settings
            records: dict of record settings 
        '''
        
        self.records = records['flow']
        self.settings = settings['flow_controller']
        self.device_name = settings['ioc']['name']
        self.FIs = self.records['controller_FIs']   # list of Flow Indicator names in channel order 
        self.FCs = self.records['controller_FCs']   # list of Flow Controller names in channel order    
        self.fc_update = dict(zip(self.FCs,[False]*len(self.FCs)))    # dict of FCs with boolean to tell thread when to update
        self.pvs = {}
        
        for pv_name in self.FIs:      # Make AIn PVs for all FIs
            self.pvs[pv_name] = aIn(pv_name)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):   # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)   # set the attributes of the PV           
        
        for pv_name in self.FCs:      # Make AOut PVs for all FCs
            self.pvs[pv_name] = aOut(pv_name, on_update_name = self.update_FC)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):   # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)   # set the attributes of the PV
                    
        self.thread = FlowThread(self)
        self.thread.start()
        
    def update_FC(self, value, pv):
        '''When PV updated, let thread know
        '''
        pv_name = pv.replace(self.device_name+':', '')   # remove device name from PV to get bare pv_name
        self.fc_update[pv_name] = True
        
class FlowThread(Thread):

    def __init__(self, parent):     
        ''' Thread reads every iteration, gets settings from parent. fc_update is boolean telling thread to change set points also.
        '''
        Thread.__init__(self)
        self.enable = parent.settings['enable'] 
        self.delay = parent.settings['delay']
        self.pvs = parent.pvs
        self.fc_update = parent.fc_update
        self.FIs = parent.FIs
        self.FCs = parent.FCs
        self.values = [0]*len(self.FIs)   # list of zeroes to start return FIs
        self.setpoints = [0]*len(self.FCs)   # list of zeroes to start readback FCs
        if self.enable:                # if not enabled, don't connect
            self.t = THCD(parent.settings['ip'], parent.settings['port'])     # open telnet connection to flow controllers

    def run(self):
        '''
        Thread to read indicator PVS from controller channels. Delay time between measurements is in seconds.
        '''
        while True:
            sleep(self.delay)
            
            for pv_name, bool in self.fc_update.items():
                if bool:   # there has been a change in this FC, update it
                    if self.enable:
                        self.t.set_setpoint(self.FCs.index(pv_name)+1, self.pvs[pv_name].get())
                    else:
                        self.setpoints[self.FCs.index(pv_name)] = self.pvs[pv_name].get()   # for test, just echo back
                    self.fc_update[pv_name] = False  
                
            if self.enable:
                self.setpoints = self.t.read_setpoints()   
                self.values = self.t.read_all()
            else:
                self.values = [random.random() for l in self.values]    # return random number when we are not enabled
            for i, pv_name in enumerate(self.FIs):
                self.pvs[pv_name].set(self.values[i])                
            for i, pv_name in enumerate(self.FCs):
                self.pvs[pv_name].set(self.setpoints[i])    

  
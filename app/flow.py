from softioc.builder import aIn, aOut

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
        #self.t = THCD(settings['ip'])
        self.FIs = self.records['controller_FI']   # list of FI names
        
        
        self.pvs = {}
        
        for pv_name in self.FIs:
            self.pvs[pv_name] = aIn(pv_name)
            for field, value in self.records[pv_name].items():
                if not isinstance(value, dict):   # don't do the lists of states
                    setattr(self.pvs[pv_name], field, value)   # set the attributes of the PV
        
    def update_FI(self):
        '''
        Read to PVS from controller
        '''        
        #list = self.t.read_all()
        #for pv_name in enumerate(FIs):
        #    self.pvs[pv_name].set(list[i])
    
    
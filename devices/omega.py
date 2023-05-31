import telnetlib
import re
from time import sleep
from softioc import builder


class Device():
    """Makes library of PVs needed for Omega iSeries and provides methods connect them to the device

    Attributes:
        pvs: dict of Process Variables keyed by name
        channels: channels of device
        new_reads: dict of most recent reads from device to set into PVs
    """

    def __init__(self, device_name, settings):
        '''Make PVs needed for this device and put in pvs dict keyed by name
        '''
        self.device_name = device_name
        self.settings = settings
        self.channels = settings['channels']
        self.pvs = {}
        self.new_reads = {}

        for channel in settings['channels']:  # set up PVs for each channel
            self.pvs[channel+'_TI'] = builder.aIn(channel+'_TI')
            self.pvs[channel+'_TC'] = builder.aOut(channel+'_TC', on_update_name=self.do_sets)

    def connect(self):
        '''Open connection to device'''
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'], self.settings['timeout'])
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        self.connect()

    def do_sets(self, new_value, pv):
        '''If PV has changed, find the correct method to set it on the device'''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        # figure out what type of PV this is, and send it to the right method
        if '_TC' in pv_name:  # is this a setpoint?
            value = self.t.set_setpoint(new_value)
            self.pvs[pv_name].set(value)  # set returned value
        else:
            print('Error, control PV not categorized.')

    def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            self.new_reads = {}
            for i, channel in enumerate(self.channels):
                self.new_reads[channel + '_TI'] = self.t.read()
        except OSError:
            self.reconnect()
        return

    def update_pvs(self):
        '''Set new values from the reads to the PVs'''
        try:
            for key, value in self.new_reads.items():
                self.pvs[key].set(value)
        except OSError:
            self.reconnect()
        except Exception as e:
            print(f"PV set failed: {e}")



class DeviceConnection():
    '''Handle connection to Omega iSeries Temperature controller over telnet. 
    '''
    def __init__(self, host, port, timeout):        
        '''Open connection to Omega
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout
        
        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)                  
        except Exception as e:
            print(f"Omega connection failed on {self.host}: {e}")
            
        self.read_regex = re.compile(b'X01(\d+.\d)')   
        self.write_regex = re.compile(b'W01')  
        self.sp_read_regex = re.compile(b'R01[\d\w]{6}')  
        #self.ok_response_regex = re.compile(b'!a!o!\s\s')    
         
    def set_setpoint(self, sp):
        '''Change setpoint 1. Seems to take a long time! Timeout needs to be at least 10 secs.'''  
        
        prefix = '*W01'    # write to sp1
        value = '{:06X}'.format(int(sp)*10+1048576*2)    # hex magic
        eol = "\r\n"
        command = prefix+value+eol
        try:     
            for char in command:
                sleep(0.1)
                self.tn.write(bytes(char,'ascii'))     
            sleep(0.5)
            i, match, data = self.tn.expect([self.write_regex], timeout=self.timeout)   # read until carriage return
            #print('command',  match, data)            
            for char in "*R01\r\n":  # readback setpoint command
                sleep(0.1)
                self.tn.write(bytes(char,'ascii'))          
            i, match, data = self.tn.expect([self.sp_read_regex], timeout=self.timeout)   # read until carriage return
            #print('data', match, data)   # read until carriage return
            m = self.pid_regex.search(data)
            values  = [float(x) for x in m.groups()]
            return values[0]
            
        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")
        
    def read(self):
        '''Read from unit.'''  
                
        command = "*X01\r\n"        
        try:
            for char in command:
                sleep(0.1)
                self.tn.write(bytes(char,'ascii'))
            i, match, data = self.tn.expect([self.read_regex], timeout=self.timeout)  # read until pattern matched
            print(match, data)
            values  = [float(x) for x in match.groups()]
            return values[0]
            
        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")

import telnetlib
import re
from time import sleep

class Omega():
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
            i, match, data = self.tn.expect([self.write_regex], timeout = self.timeout)   # read until carriage return 
            #print('command',  match, data)            
            for char in "*R01\r\n":  # readback setpoint command
                sleep(0.1)
                self.tn.write(bytes(char,'ascii'))          
            i, match, data = self.tn.expect([self.sp_read_regex], timeout = self.timeout)   # read until carriage return 
            #print('data', match, data)   # read until carriage return
            #m = self.pid_regex.search(data)
            #values  = [float(x) for x in m.groups()]
            #return values
            
        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")
        
    def read_temp(self):
        '''Read from unit.'''  
                
        command = "*X01\r\n"        
        try: 
            #self.tn.write(bytes('*X01','ascii'))     # 0 means it will return all channels  
            for char in command:
                sleep(0.1)
                self.tn.write(bytes(char,'ascii'))     # 0 means it will return all channels   
            #data = self.tn.read_until(b'\n', timeout = self.timeout).decode('ascii')   # read until carriage return
            i, match, data = self.tn.expect([self.read_regex], timeout = self.timeout)  # read until pattern matched
            print(match, data)
            values  = [float(x) for x in match.groups()]
            return values[0]
            
        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")
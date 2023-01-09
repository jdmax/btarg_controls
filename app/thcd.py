import telnetlib
import re

class THCD():
    '''Handle connection to Teledyne Hastings THCD-401 via Telnet. 
    
    Arguments:
        host: IP address of device
    '''
    def __init__(self, host,):        
        '''Open connection to R&S, send commands for all settings, and read all back to check. Close.
        Arguments:
            host: IP address
        '''
        self.host = host
        #self.host = '192.168.1.180'
        self.port = '101'
        
        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=2)      
            #tn.write(bytes(f"FREQ {config.channel['cent_freq']*1000000}\n", 'ascii'))
            #tn.write(bytes(f"POWer {config.channel['power']} mV\n", 'ascii'))
            #out = self.tn.read_some().decode('ascii')              
        except Exception as e:
            print(f"THCD connection failed on {self.host}: {e}")
            
        self.read_regex = re.compile('READ:(\d+.\d+),(\d+.\d+),(\d+.\d+),(\d+.\d+),')  
        self.set_regex = re.compile('SP(\d) VALUE: (\d+.\d+)')    
        
    def read_all(self):
        '''Read all channels. Returns list of 4 readings.'''        
        try:
            self.tn.write(b"ar\n")
            out1 = self.tn.read_until(b"\n").decode('ascii') 
            out2 = self.tn.read_until(b"\n").decode('ascii')
            m = self.read_regex.match(out1)
            values = m.groups()
            values  = [float(x) for x in values]
            return values
            
        except Exception as e:
            print(f"THCD read failed on {self.host}: {e}")
        
    def set_setpoint(self, channel, value):
        '''Set set points for given channel. Returns list of 4 setpoints after setting.'''        
        try:
            self.tn.write(bytes(f"aspv {channel},{value}\n",'ascii'))            
            out1 = self.tn.read_until(b"\n").decode('ascii') 
            out2 = self.tn.read_until(b"\n").decode('ascii') 
            #print(out1, out2)            
            self.tn.write(bytes(f"aspv?\n",'ascii'))
            out1 = self.tn.read_until(b"\n").decode('ascii') \
                + self.tn.read_until(b"\n").decode('ascii') \
                + self.tn.read_until(b"\n").decode('ascii') \
                + self.tn.read_until(b"\n").decode('ascii') \
                + self.tn.read_until(b"\n").decode('ascii') \
                + self.tn.read_until(b"\n").decode('ascii') 
            #print(out1)            
            ms = self.set_regex.findall(out1)
            values = []
            for m in ms:
                values.append(float(m[1]))
            return values   
            
        except Exception as e:
            print(f"THCD write setpoint failed on {self.host}: {e}")
        
    def read_setpoints(self):
        '''Read set points for all channels. Returns list of 4 setpoints.'''     
        values = []
        try:
            self.tn.write(bytes(f"aspv?\n",'ascii'))
            out1 = self.tn.read_until(b"!a!").decode('ascii') 
            #print(out1)
            ms = self.set_regex.findall(out1)
            for m in ms:
                values.append(float(m[1]))
            return values    
            
            
        except Exception as e:
            print(f"THCD read setpoint failed on {self.host}: {e}")
         
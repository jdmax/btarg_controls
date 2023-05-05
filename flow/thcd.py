import telnetlib
import re

class THCD():
    '''Handle connection to Teledyne Hastings THCD-401 via Telnet.     
    '''
    def __init__(self, host, port, timeout):        
        '''Open connection to Flow Controller
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
            print(f"THCD connection failed on {self.host}: {e}")
            
        self.read_regex = re.compile('READ:(-*\d+.\d+|!RANGE!),(-*\d+.\d+|!RANGE!),(-*\d+.\d+|!RANGE!),(-*\d+.\d+)|!RANGE!,')
        self.set_regex = re.compile('SP(\d) VALUE: (\d+.\d+)')  
        self.ok_response_regex = re.compile(b'!a!o!\s\s')    
        
    def read_all(self):
        '''Read all channels. Returns list of 4 readings.'''        
        try:
            self.tn.write(b"ar\n")
            i, match, data = self.tn.expect([self.ok_response_regex], timeout = 2)   # read until ok response
            out = data.decode('ascii')
            m = self.read_regex.search(out)
            values = [float(x) if not 'RANGE' in x else 999 for x in m.groups()]
            return values
            
        except Exception as e:
            raise OSError('THCD read')
            print(f"THCD read failed on {self.host}: {e}")
        
    def set_setpoint(self, channel, value):
        '''Set set points for given channel. Returns list of 4 setpoints after setting.'''        
        try:
            self.tn.write(bytes(f"aspv {channel},{value}\n",'ascii'))   
            i, match, data = self.tn.expect([self.ok_response_regex], timeout = 2) 
            return True
            
        except Exception as e:
            raise OSError('THCD write SP')
            print(f"THCD write setpoint failed on {self.host}: {e}")
        
    def read_setpoints(self):
        '''Read set points for all channels. Returns list of 4 setpoints.'''     
        values = []
        try:
            self.tn.write(bytes(f"aspv?\n",'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout = 2) 
            out = data.decode('ascii')
            #print(out)
            ms = self.set_regex.findall(out)
            for m in ms:
                values.append(float(m[1]))
            return values              
            
        except Exception as e:
            raise OSError('THCD read SP')
            print(f"THCD read setpoint failed on {self.host}: {e}")

    def __del__(self):
        try:
            self.tn.close()
        except Exception as e:
            print(e)
         
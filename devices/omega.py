import telnetlib
import re
from time import sleep
from softioc import builder, alarm


class Device():
    """Makes library of PVs needed for Omega iSeries and provides methods connect them to the device

    Attributes:
        pvs: dict of Process Variables keyed by name
        channels: channels of device
    """

    def __init__(self, device_name, settings):
        '''Make PVs needed for this device and put in pvs dict keyed by name
        '''
        self.device_name = device_name
        self.settings = settings
        self.channels = settings['channels']
        self.pvs = {}
        sevr = {'HHSV': 'MAJOR', 'HSV': 'MINOR', 'LSV': 'MINOR', 'LLSV': 'MAJOR', 'DISP': '0'}

        for channel in settings['channels']:  # set up PVs for each channel
            if "None" in channel: continue
            self.pvs[channel+'_TI'] = builder.aIn(channel+'_TI', **sevr)
            self.pvs[channel+'_SP1'] = builder.aOut(channel+'_SP1', on_update_name=self.do_sets, **sevr)
            self.pvs[channel+'_SP2'] = builder.aOut(channel+'_SP2', on_update_name=self.do_sets, **sevr)

    async def connect(self):
        '''Open connection to device'''
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'], self.settings['timeout'])
            await self.read_outs()
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    async def read_outs(self):
        """Read OUT PVs at the start of the IOC"""
        for i, pv_name in enumerate(self.channels):
            try:
                print("setting outs from device")
                self.pvs[pv_name+'_SP1'].set(self.t.read_setpoint1())  # set returned value
                self.pvs[pv_name+'_SP2'].set(self.t.read_setpoint2())  # set returned value
                print("done setting outs from device")
            except OSError:
                await self.reconnect()
        return

    async def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        await self.connect()

    async def do_sets(self, new_value, pv):
        '''If PV has changed, find the correct method to set it on the device'''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        # figure out what type of PV this is, and send it to the right method
        try:
            if '_SP1' in pv_name:
                new = self.t.set_setpoint1(new_value)
                #print(new, pv_name)
                self.pvs[pv_name].set(new)  # set returned value
            if '_SP2' in pv_name:
                new = self.t.set_setpoint2(new_value)
                #print(new, pv_name)
                self.pvs[pv_name].set(new)  # set returned value
            else:
                print('Error, control PV not categorized.')
        except OSError:
            await self.reconnect()
        return

    async def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.pvs[channel + '_TI'].set(self.t.read())
                self.remove_alarm(channel + '_TI')
        except (OSError, TypeError):
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.set_alarm(channel+ '_TI')
            await self.reconnect()
        else:
            return True

    def set_alarm(self, channel):
        """Set alarm and severity for channel"""
        self.pvs[channel].set_alarm(severity=1, alarm=alarm.READ_ALARM)

    def remove_alarm(self, channel):
        """Remove alarm and severity for channel"""
        self.pvs[channel].set_alarm(severity=0, alarm=alarm.NO_ALARM)


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
            
        self.read_regex = re.compile(b'X01(-?\d+\.\d)')
        self.write_regex = re.compile(b'W01')  
        self.sp_read_regex = re.compile(b'R01([\d\w]{6})')
        self.sp2_read_regex = re.compile(b'R02([\d\w]{6})')
        #self.ok_response_regex = re.compile(b'!a!o!\s\s')    

    def set_setpoint1(self, sp):
        '''Change setpoint 1. Seems to take a long time! Timeout needs to be at least 10 secs.'''

        prefix = '*W01'  # write to sp1
        value = '{:06X}'.format(int(sp) * 10 + 1048576 * 2)  # hex magic
        # comes from an example on github: rval='{:06X}'.format(int(val)*10+1048576*2)
        eol = "\r\n"
        command = prefix + value + eol
        try:
            for char in command:
                sleep(0.1)
                self.tn.write(bytes(char, 'ascii'))
            sleep(0.5)
            i, match, data = self.tn.expect([self.write_regex], timeout=self.timeout)  # read until carriage return
            # print('command',  match, data)
            return self.read_setpoint1()

        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")

    def set_setpoint2(self, sp):
        '''Change setpoint 1. Seems to take a long time! Timeout needs to be at least 10 secs.'''

        prefix = '*W02'  # write to sp1
        value = '{:06X}'.format(int(sp) * 10 + 1048576 * 2)  # hex magic
        eol = "\r\n"
        command = prefix + value + eol
        try:
            for char in command:
                sleep(0.1)
                self.tn.write(bytes(char, 'ascii'))
            sleep(0.5)
            i, match, data = self.tn.expect([self.write_regex], timeout=self.timeout)  # read until carriage return
            # print('command',  match, data)
            return self.read_setpoint2()

        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")

    def read_setpoint1(self):
        '''Read back setpoint.'''
        try:
            for char in "*R01\r\n":  # readback setpoint command
                sleep(0.1)
                self.tn.write(bytes(char, 'ascii'))
            i, match, data = self.tn.expect([self.sp_read_regex], timeout=self.timeout)  # read until carriage return
            #print('data1', match, data)   # read until carriage return
            m = self.sp_read_regex.search(data)
            new = m.groups()[0]
            sp = (int(new,16) - 1048576 * 2)/10   # hex magic backwards
            return sp

        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")
    def read_setpoint2(self):
        '''Read back setpoint.'''
        try:
            for char in "*R02\r\n":  # readback setpoint command
                sleep(0.1)
                self.tn.write(bytes(char,'ascii'))
            i, match, data = self.tn.expect([self.sp2_read_regex], timeout=self.timeout)   # read until carriage return
            #print('data2', match, data)   # read until carriage return
            m = self.sp2_read_regex.search(data)
            new = m.groups()[0]
            sp = (int(new,16) - 1048576 * 2)/10
            return sp

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
            #print(match, data)
            values  = [float(x) for x in match.groups()]
            return values[0]
            
        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")

import telnetlib
import re
import time
from softioc import builder


class Device():
    '''Makes library of PVs needed for Rigol DP832 and provides methods connect them to the device

    Attributes:
        pvs: dict of Process Variables keyed by name
        channels: channels of device
        new_reads: dict of most recent reads from device to set into PVs
    '''
    def __init__(self, device_name, settings):
        '''Make PVs needed for this device and put in pvs dict keyed by name
        '''
        self.device_name = device_name
        self.settings = settings
        self.channels = settings['channels']
        self.pvs = {}
        self.new_reads = {}

        for channel in settings['channels']:  # set up PVs for each channel
            if "None" in channel: continue
            self.pvs[channel+"_VI"] = builder.aIn(channel+"_VI")   # Voltage
            self.pvs[channel+"_CI"] = builder.aIn(channel+"_CI")   # Current

            self.pvs[channel + "_CC"] = builder.aOut(channel + "_CC", on_update_name=self.do_sets)
            self.pvs[channel + "_VC"] = builder.aOut(channel + "_VC", on_update_name=self.do_sets)

            self.pvs[channel + "_Mode"] = builder.boolOut(channel + "_Mode", on_update_name=self.do_sets)


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
        """Set PVs values to device"""
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        p = pv_name.split("_")[0]  # pv_name root
        chan = self.channels.index(p) + 1  # determine what channel we are on
        # figure out what type of PV this is, and send it to the right method
        if 'CC' in pv_name or 'VC' in pv_name:  # is this a current set? Voltage set from settings file
            values = self.t.set(chan, self.pvs[p + '_VC'].get(), self.pvs[p + '_CC'].get())
            self.pvs[p + '_VC'].set(values[0])  # set returned voltage
            self.pvs[p + '_CC'].set(values[1])  # set returned current
        elif 'Mode' in pv_name:
            value = self.t.set_state(chan, self.pvs[pv_name].get())
            self.pvs[pv_name].set(int(value))  # set returned value
        else:
            print('Error, control PV not categorized.', pv_name)

    def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            new_reads = {}
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                new_reads[channel+'_VI'], new_reads[channel+'_CI'], power = self.t.read(i+1)
                new_reads[channel+'_VC'], new_reads[channel+'_CC'] = self.t.read_sp(i+1)
                new_reads[channel+'_Mode'] = self.t.read_state(i+1)

            for key, value in new_reads.items():
                self.pvs[key].set(value)
        except OSError:
            self.reconnect()
        return


class DeviceConnection():
    '''Handle connection to Rigol DP832 via Telnet.
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to Rigol DP832, required LAN option unlocked.
        30V/3A on Ch1, Ch2. 5V/3A Ch3.
        Arguments:
            host: IP address
        port: Port of device
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
        except Exception as e:
            print(f"DP832 connection failed on {self.host}: {e}")

        self.read_regex = re.compile('CH\d:\d+V/\dA,(\d+.\d+),(\d+.\d+)')
        self.read_sp_regex = re.compile('(\d+.\d+),(\d+.\d+),(\d+.\d+)')

    def read_sp(self, channel):
        '''Read voltage, current measured for given channel (1,2,3).'''
        try:
            command = f":APPLY? CH{channel}\n"
            self.tn.write(bytes(command, 'ascii'))   # Reading
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')  # read until carriage return
            m = self.read_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values   # return voltage, current as list

        except Exception as e:
            print(f"DP832 read sp failed on {self.host}: {e},{command},{data}")
            raise OSError('DP832 read sp')

    def read(self, channel):
        '''Read voltage, current measured for given channel (1,2,3).'''
        try:
            command = f":MEASURE:ALL? CH{channel}\n"
            self.tn.write(bytes(command, 'ascii'))   # Reading
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')  # read until carriage return
            m = self.read_sp_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values   # return voltage, current as list

        except Exception as e:
            print(f"DP832 read failed on {self.host}: {e}, {command},{data}")
            raise OSError('DP832 read')

    def set(self, channel, voltage, current):
        '''Set current and voltage for given channel'''
        try:
            self.tn.write(bytes(f":APPLY CH{channel},{voltage},{current}\n", 'ascii'))
            time.sleep(0.2)
            return self.read_sp(channel)   # return voltage, current as list

        except Exception as e:
            print(f"DP832 set failed on {self.host}: {e}")
            raise OSError('DP832 set')


    def read_state(self, channel):
        '''Read output state for given channel.
        Arguments:
            channel: out put channel (1 to 4)
        '''
        try:
            self.tn.write(bytes(f"OUTPUT? CH{channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')  # read until carriage return
            state = True if 'ON' in data else False
            return state

        except Exception as e:
            print(f"DP832 outmode read failed on {self.host}: {e}")
            raise OSError('DP832 outmode read')

    def set_state(self, channel, state):
        '''Setup output state on (true) or off (false).
        Arguments:
            channel: out put channel (1 to 4)
            state: False=Off, True=On
        '''
        out = 'ON' if state else 'OFF'
        try:
            self.tn.write(bytes(f":OUTPUT CH{channel},{out}\n", 'ascii'))
            time.sleep(0.2)
            return self.read_state(channel)
        except Exception as e:
            print(f"DP832 out set failed on {self.host}: {e}")
            raise OSError('DP832 out set')

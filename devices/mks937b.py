import telnetlib
import re
from softioc import builder, alarm


class Device():
    """Makes library of PVs needed for MKS937b and provides methods connect them to the device

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
            self.pvs[channel] = builder.aIn(channel, **sevr)
            if 'CC' in channel:   # Cold cathode channels need DI for off/on
                self.pvs[channel + '_DI'] = builder.aIn(channel + '_DI', **sevr)

    async def connect(self):
        """Open connection to device"""
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'],
                                      self.settings['address'], self.settings['timeout'])
            await self.read_outs()
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    async def read_outs(self):
        """Read and set OUT PVs at the start of the IOC"""
        for i, channel in enumerate(self.settings['channels']):  # set up PVs for each channel
            if 'CC' in channel:
                try:
                    power_status = self.t.read_power(i+1)
                    self.pvs[channel+"_DI"].set(power_status)  # set returned value
                except OSError:
                    await self.reconnect()

    async def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        await self.connect()

    async def do_sets(self, new_value, pv):
        '''If PV has changed, find the correct method to set it on the device'''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        #p = pv_name.split("_")[0]  # pv_name root
        chan = self.channels.index(pv_name) + 1  # determine what channel we are on
        # figure out what type of PV this is, and send it to the right method
        print(pv, pv_name, chan)
        try:
            if '_DI' in pv_name:
                self.pvs[pv_name].set(self.t.set_power(chan, new_value))
            else:
                print('Error, control PV not categorized.')
        except OSError:
            await self.reconnect()
        return

    async def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            pres = self.t.read_all()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.pvs[channel].set(pres[i])
                self.remove_alarm(channel)
        except OSError:
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.set_alarm(channel)
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
    '''Handle connection to MKS 937B pressure gauge controller via ethernet to serial adapter.
    '''

    def __init__(self, host, port, address, timeout):
        '''Open connection to MKS
        Arguments:
            host: IP address
            port: Port of device
        '''
        self.host = host
        self.port = port
        self.address = address
        self.timeout = timeout

        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
        except Exception as e:
            print(f"MKS 937B connection failed on {self.host}: {e}")

        self.read_regex = re.compile('ACK(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*);FF')
        self.read_power_regex = re.compile('ACK(ON|OFF);FF')

    def read_all(self):
        '''Read pressures for all channels.'''
        try:
            command = "@" + self.address + "PRZ?;FF"  # @003PRZ?;FF
            self.tn.write(bytes(command, 'ascii'))
            data = self.tn.read_until(b';FF', timeout=self.timeout).decode('ascii')
            m = self.read_regex.search(data)
            values = []
            for x in m.groups():
                if 'ATM' in x:
                    values.append(760.0)
                elif 'LO<' in x:
                    values.append(0.0)
                else:
                    try:
                        values.append(float(x))
                    except ValueError:
                        values.append(9999)
            return values

        except Exception as e:
            print(f"MKS 937B read failed on {self.host}: {e}")
            raise OSError('MKS 937B read')

    def read_power(self, channel):
        '''Read sensor power status for given channel. channel can be 1, 3 or 5'''
        try:
            command = f"@{self.address}CP{channel}?;FF"
            self.tn.write(bytes(command, 'ascii'))
            data = self.tn.read_until(b';FF', timeout=self.timeout).decode('ascii')
            m = self.read_power_regex.search(data)
            if 'ON' in m.groups()[0]:
                return True
            else:
                return False

        except Exception as e:
            print(f"MKS 937B power read failed on {self.host}: {e}")
            raise OSError('MKS 937B power read')

    def set_power(self, channel, value):
        '''Set sensor power status for given channel. channel can be 1, 3 or 5'''
        power = "ON" if value else "OFF"
        try:
            command = f"@{self.address}CP{channel}!{power};FF"
            self.tn.write(bytes(command, 'ascii'))
            data = self.tn.read_until(b';FF', timeout=self.timeout).decode('ascii')
            m = self.read_power_regex.search(data)
            if 'ON' in m.groups()[0]:
                return True
            else:
                return False

        except Exception as e:
            print(f"MKS 937B power set failed on {self.host}: {e}")
            raise OSError('MKS 937B power set')

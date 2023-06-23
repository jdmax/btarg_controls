import telnetlib
import re
from softioc import builder


class Device():
    """Makes library of PVs needed for THCD-401 and provides methods connect them to the device

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
        sevr = {'HHSV': 'MAJOR', 'HSV': 'MINOR', 'LSV': 'MINOR', 'LLSV': 'MAJOR', 'DISP': '0'}

        mode_list = [['Auto', 0], ['Open', 1], ['Closed', 2]]

        for channel in settings['channels']:  # set up PVs for each channel
            if "_FI" in channel:
                self.pvs[channel] = builder.aIn(channel, **sevr)
            elif "None" in channel:
                pass
            else:
                self.pvs[channel + "_FI"] = builder.aIn(channel + "_FI", **sevr)
                self.pvs[channel + "_FC"] = builder.aOut(channel + "_FC", on_update_name=self.do_sets, **sevr)
                self.pvs[channel + "_Mode"] = builder.mbbOut(channel + "_Mode", *mode_list, on_update_name=self.do_sets)

    def connect(self):
        """Open connection to device"""
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'], self.settings['timeout'])
            self.read_outs()
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    def read_outs(self):
        """Read and set OUT PVs at the start of the IOC"""
        sps = self.t.read_setpoints()
        modes = self.t.read_modes()
        for i, channel in enumerate(self.settings['channels']):  # set up PVs for each channel
            try:
                self.pvs[channel+"_FC"].set(sps[i])  # set returned value
                self.pvs[channel+"_Mode"].set(modes[i])  # set returned value
            except OSError:
                self.reconnect()

    def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        self.connect()

    def do_sets(self, new_value, pv):
        '''If PV has changed, find the correct method to set it on the device'''
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        p = pv_name.split("_")[0]  # pv_name root
        chan = self.channels.index(p) + 1  # determine what channel we are on
        # figure out what type of PV this is, and send it to the right method
        try:
            if '_FC' in pv_name:
                self.pvs[pv_name].set(self.t.set_setpoint(chan, new_value))
            elif '_Mode' in pv_name:
                self.pvs[pv_name].set(self.t.set_mode(chan, new_value))
            else:
                print('Error, control PV not categorized.')
            self.pvs[pv_name + '.STAT'].set('')
        except OSError:
            self.pvs[pv_name + '.STAT'].set('WRITE')
            self.reconnect()
        return

    def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            flows = self.t.read_all()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.pvs[channel].set(flows[i])
                self.pvs[channel + '.STAT'].set('')
        except OSError:
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.pvs[channel + '.STAT'].set('READ')
            self.reconnect()
        return


class DeviceConnection():
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

        self.read_regex = re.compile(
            'READ:(-*\d+.\d+|!RANGE!),(-*\d+.\d+|!RANGE!),(-*\d+.\d+|!RANGE!),(-*\d+.\d+)|!RANGE!,')
        self.set_regex = re.compile('SP(\d) VALUE: (\d+.\d+)')
        self.mode_regex = re.compile('SP(\d) MODE: \((\d)\)')
        self.ok_response_regex = re.compile(b'!a!o!\s\s')

    def read_all(self):
        '''Read all channels. Returns list of 4 readings.'''
        try:
            self.tn.write(b"ar\n")
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)  # read until ok response
            out = data.decode('ascii')
            m = self.read_regex.search(out)
            values = [float(x) if not 'RANGE' in x else 999 for x in m.groups()]
            return values

        except Exception as e:
            print(f"THCD read failed on {self.host}: {e}")
            raise OSError('THCD read')

    def set_setpoint(self, channel, value):
        '''Set set points for given channel.'''
        try:
            command = f"aspv {channel},{value:.2f}\n"
            self.tn.write(bytes(command, 'ascii'))
            print(command)
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)
            return self.read_setpoints()[int(channel)-1]

        except Exception as e:
            print(f"THCD write setpoint failed on {self.host}: {e}")
            raise OSError('THCD write SP')

    def read_setpoints(self):
        '''Read set points for all channels. Returns list of 4 setpoints.'''
        values = []
        try:
            self.tn.write(bytes(f"aspv?\n", 'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)
            out = data.decode('ascii')
            # print(out)
            ms = self.set_regex.findall(out)
            for m in ms:
                values.append(float(m[1]))
            return values

        except Exception as e:
            print(f"THCD read setpoint failed on {self.host}: {e}")
            raise OSError('THCD read SP')

    def set_mode(self, channel, value):
        '''Set mode for given channel.'''
        try:
            self.tn.write(bytes(f"aspm {channel},{value}\n", 'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)
            return self.read_modes()[int(channel)-1]

        except Exception as e:
            print(f"THCD write mode failed on {self.host}: {e}")
            raise OSError('THCD write mode')

    def read_modes(self):
        '''Read modes for all channels. Returns list of 4.'''
        values = []
        try:
            self.tn.write(bytes(f"aspm?\n", 'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)
            out = data.decode('ascii')
            ms = self.mode_regex.findall(out)
            for m in ms:
                values.append(int(m[1]))
            return values
        except Exception as e:
            print(f"THCD read modes failed on {self.host}: {e}")
            raise OSError('THCD read mode')

    def __del__(self):
        try:
            self.tn.close()
        except Exception as e:
            print(e)


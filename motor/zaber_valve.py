import asyncio
from zaber_motion import Units
from zaber_motion.ascii import Connection


class MotorController():
    '''Handle connection to Zaber motor controller for all axes
    '''

    def __init__(self, host):
        '''Open connection to motor controller
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.axes = []

        try:
            self.con = Connection.open_tcp(host, Connection.TCP_PORT_CHAIN)
            device_list = self.con.detect_devices()
            device = device_list[0]
            for i in range(0, device.axis_count):
                self.axes.append(device.get_axis(i+1))
        except Exception as e:
            print(f"Zaber motor connection failed on {self.host}: {e}")

    def move_to(self, axis, location):
        self.axes[axis].move_absolute(location, Units.ANGLE_DEGREES)

    def move_relative(self, axis, degrees):
        self.axes[axis].move_relative(degrees, Units.ANGLE_DEGREES)

    def stop(self, axis):
        self.axes[axis].stop()

    def home(self, axis):
        self.axes[axis].home()

    def away(self, axis):
        self.axes[axis].generic_command('tools gotolimit away pos 1 0')

# from zaber example:
#axis1_coroutine = axis1.move_absolute_async(3, Units.LENGTH_CENTIMETRES)
#axis2_coroutine = axis2.move_absolute_async(3, Units.LENGTH_CENTIMETRES)

#move_coroutine = asyncio.gather(axis1_coroutine, axis2_coroutine)

#loop = asyncio.get_event_loop()
#loop.run_until_complete(move_coroutine)
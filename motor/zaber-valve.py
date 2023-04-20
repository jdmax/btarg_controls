import asyncio
from zaber_motion.ascii import Connection


class Motor():
    '''Handle connection to Zaber motor controller.
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to motor controller
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.con = Connection.open_tcp(host, Connection.TCP_PORT_CHAIN)
        except Exception as e:
            print(f"Zaber motor connection failed on {self.host}: {e}")


    def home(self, channel):

    def move_to(self):
# from zaber example:
axis1_coroutine = axis1.move_absolute_async(3, Units.LENGTH_CENTIMETRES)
axis2_coroutine = axis2.move_absolute_async(3, Units.LENGTH_CENTIMETRES)

move_coroutine = asyncio.gather(axis1_coroutine, axis2_coroutine)

loop = asyncio.get_event_loop()
loop.run_until_complete(move_coroutine)
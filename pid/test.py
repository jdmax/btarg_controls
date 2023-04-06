import asyncio
from aioca import caget, caput, camonitor, run
from softioc import softioc, builder, asyncio_dispatcher

async def main():
    '''
    Run PID IOC: load settings, create dispatcher, set name, start loops, do IOC boilerplate
    '''
    print('TGT:BTARG:PID:Test_Power', await caget('TGT:BTARG:PID:Test_Power'))

    #dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    #device_name = 'TEST'
    #builder.SetDeviceName(device_name)

    #builder.LoadDatabase()
    #softioc.iocInit(dispatcher)

    #softioc.interactive_ioc(globals())

if __name__ == "__main__":
    asyncio.run(main())
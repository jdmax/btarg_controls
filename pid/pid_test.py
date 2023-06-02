from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml
import argparse
import os

async def main():
    '''
    Run PI Test IOC: load settings, create dispatcher, set name, start devices, do boilerplate
    '''
    settings = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['all_iocs']['prefix'] + ':PID'
    builder.SetDeviceName(device_name)

    p = BoilerControl(device_name)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    async def loop():
        while True:
            await p.update()

    dispatcher(loop)  # put functions to loop in here

    softioc.interactive_ioc(globals())


class BoilerControl():
    '''Set up PVs for relays and connect to device
    '''

    def __init__(self, device_name):
        '''   '''

        self.water_temp = 20
        self.boiler_power = 5
        self.dt = 1
        self.in_pv = builder.aIn('Test_Temp')
        setattr(self.in_pv, 'HIHI', 50.0)
        setattr(self.in_pv, 'HHSV', 'MAJOR')
        setattr(self.in_pv, 'HIGH', 40.0)
        setattr(self.in_pv, 'HSV', 'MINOR')
        setattr(self.in_pv, 'LOW', 20.0)
        setattr(self.in_pv, 'LSV', 'MINOR')
        setattr(self.in_pv, 'LOLO', 10.0)
        setattr(self.in_pv, 'LLSV', 'MAJOR')
        self.out_pv = builder.aOut('Test_Power', DRVL = 0.0, DRVH = 50.0, on_update=self.set, always_update=True)
        self.out_pv.set(self.boiler_power)


    def set(self, power):
        self.boiler_power = power

    async def update(self):
        await asyncio.sleep(self.dt)
        self.water_temp += 1 * self.boiler_power * self.dt
        print(self.water_temp, self.boiler_power)

        # Some heat dissipation
        self.water_temp -= 5 * self.dt
        self.in_pv.set(self.water_temp)
        print('Temp', self.water_temp)


def load_settings():
    '''Load device settings and records from YAML settings files. Argument parser allows '-s' to give a different folder'''

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--Settings", help = "Settings files folder")
    args = parser.parse_args()
    folder = args.Settings if args.Settings else '..'

    with open(f'{folder}/settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/settings.yaml.")

    return settings


if __name__ == "__main__":
    asyncio.run(main())
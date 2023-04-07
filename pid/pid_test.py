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
    device_name = settings['prefix'] + ':PID'
    builder.SetDeviceName(device_name)

    p = BoilerControl(device_name)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class BoilerControl():
    '''Set up PVs for relays and connect to device
    '''

    def __init__(self, device_name):
        '''   '''

        self.water_temp = 20
        self.dt = 0.5
        self.in_pv = builder.aIn('Test_Temp')
        self.out_pv = builder.aOut('Test_Power', DRVL = 0.0, DRVH = 50.0, on_update=self.update, always_update=True)


    def update(self, boiler_power):
        #if boiler_power > 0:
            # Boiler can only produce heat, not cold
        self.water_temp += 1 * boiler_power * self.dt

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
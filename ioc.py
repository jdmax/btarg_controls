from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import yaml

async def main():
    '''
    Run IOCs: load settings, create dispatcher, set name, start devices, do boilerplate. All based on settings.
    '''
    settings, records = load_settings()

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    device_name = settings['prefix'] + ':PRES'
    builder.SetDeviceName(device_name)

    p = ReadMKS(device_name, settings['mks937b'], records)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


def load_settings():
    '''Load device settings and records from YAML settings files. Argument parser allows '-s' to give a different folder'''

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--Settings", help = "Settings files folder")
    args = parser.parse_args()
    folder = args.Settings if args.Settings else '..'

    with open(f'{folder}/settings.yaml') as f:  # Load settings from YAML files
        settings = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded device settings from {folder}/settings.yaml.")

    with open(f'{folder}/records.yaml') as f:  # Load settings from YAML files
        records = yaml.load(f, Loader=yaml.FullLoader)
    print(f"Loaded records from {folder}/records.yaml.")

    return settings, records


if __name__ == "__main__":
    asyncio.run(main())
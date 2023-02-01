import screenutils
import yaml

with open('../settings.yaml') as f:  # Load settings from YAML files
    settings = yaml.load(f, Loader=yaml.FullLoader)
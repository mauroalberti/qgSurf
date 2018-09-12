import yaml


def read_yaml(file_pth):

    return yaml.safe_load(open(file_pth).read())


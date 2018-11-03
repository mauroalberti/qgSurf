
from typing import Dict

import yaml


def read_yaml(file_pth: str) -> Dict:

    return yaml.safe_load(open(file_pth).read())



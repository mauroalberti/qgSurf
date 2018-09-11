
import os
import yaml

tools_config_file = r"C:\Users\mauro\Documents\projects\qgSurf\config\plugin.yaml"
tools_params = yaml.safe_load(open(tools_config_file).read())

print(type(tools_params))
print(tools_params)

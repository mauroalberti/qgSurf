
import yaml

db_config_file = "/home/mauro/Documents/projects/qgSurf/config/output.yaml"

output_params = yaml.safe_load(open(db_config_file).read())

shape_pars = output_params["pt_shapefile"]

print(type(shape_pars))
print(len(shape_pars))
for par in shape_pars:
    print(par)

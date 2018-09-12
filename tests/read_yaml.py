
import yaml

db_config_file = r"C:\Users\mauro\Documents\projects\qgSurf\config\sqlite.yaml"
db_params = yaml.safe_load(open(db_config_file).read())
sqlite_params = db_params["sqlite_db"]

db_name = sqlite_params["name"]
db_folder = sqlite_params["folder"]
tables = sqlite_params["tables"]

solutions_pars = tables["solutions"]
src_points_pars = tables["src_pts"]

solutions_tbl_nm = solutions_pars["name"]
solutions_tbl_flds = solutions_pars["fields"]

print(db_name)
print(db_folder)
print(solutions_tbl_nm)

for fld in solutions_tbl_flds:
    print(fld["name"], fld["type"])

flds_string = ",".join(map(lambda fld: "{} {}".format(fld["name"], fld["type"]), solutions_tbl_flds))

print(flds_string)

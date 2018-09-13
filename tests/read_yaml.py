
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
print(solutions_tbl_flds)

flds_parts = []
for dct in solutions_tbl_flds:
    fld_ident = list(dct.keys())[0]
    flds_parts.append("{} {}".format(dct[fld_ident]["name"], dct[fld_ident]["type"]))

flds_string = ", ".join(flds_parts)

print(flds_string)

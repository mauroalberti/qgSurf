
ID_SOL, DIP_DIR, DIP_ANG, DATASET, NOTES, SRC_CRS, CREAT_TIME = range(7)
ID_PT, FK_ID_SOL, PT_INT_ID, X, Y, Z, LON, LAT = range(8)

solutions_flds_str = "id, dip_dir, dip_ang, data_set, notes, src_crs, creat_time"
source_points_flds_str = "id, id_sol, pt_int_id, x, y, z, longitude, latitude"

select_from_template = "SELECT %s FROM {}"
generic_where_in_template = " WHERE {} IN ({})"

check_query_template = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'"
query_sol_id_template = "select {id} from {solutions} where {creat_time} = (select MAX({creat_time}) from {solutions})"

query_solutions_all_template = "SELECT {}, {} FROM {}"
query_solutions_selection_template = query_solutions_all_template + generic_where_in_template

xprt_shppt_select_all_results = """
SELECT src_points.id, src_points.id_sol, src_points.pt_int_id, 
       src_points.x, src_points.y, src_points.z, 
       src_points.longitude, src_points.latitude, 
       solutions.dip_dir, solutions.dip_ang, solutions.data_set, solutions.notes, 
       solutions.src_crs, solutions.creat_time
FROM src_points 
INNER JOIN solutions
ON src_points.id_sol = solutions.id 
ORDER BY src_points.id
"""

xprt_shppt_select_part_results = """
SELECT src_points.id, src_points.id_sol, src_points.pt_int_id, 
       src_points.x, src_points.y, src_points.z, 
       src_points.longitude, src_points.latitude, 
       solutions.dip_dir, solutions.dip_ang, solutions.data_set, solutions.notes, 
       solutions.src_crs, solutions.creat_time
FROM src_points 
INNER JOIN solutions
ON src_points.id_sol = solutions.id 
WHERE src_points.id_sol IN ({})
ORDER BY src_points.id
"""

select_all_solutions_ids = """
SELECT id
FROM solutions
ORDER BY id ASC
"""

select_solution_pars_template = """
SELECT dip_dir, dip_ang, data_set, notes, src_crs, creat_time
FROM solutions
WHERE id = {}
"""

xprt_shpln_select_sol_pts_pars_template = """
SELECT x, y, z
FROM src_points
WHERE id_sol = {}
ORDER BY pt_int_id
"""


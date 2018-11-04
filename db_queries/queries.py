
solutions_flds_str = "id, dip_dir, dip_ang, label, comments, creat_time"
source_points_flds_str = "id, id_sol, x, y, z"

select_from_template = "SELECT %s FROM {}"
generic_where_in_template = " WHERE {} IN ({})"

check_query_template = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'"
query_sol_id_template = "select {id} from {solutions} where {creat_time} = (select MAX({creat_time}) from {solutions})"

query_solutions_all_template = "SELECT {}, {} FROM {}"
query_solutions_selection_template = query_solutions_all_template + generic_where_in_template

query_solutions_fllattr_full_template = select_from_template % solutions_flds_str
query_solutions_fllattr_selection_template = query_solutions_fllattr_full_template + generic_where_in_template

query_points_fllattr_full_template = select_from_template % source_points_flds_str
query_points_fllattr_selection_template = query_points_fllattr_full_template + generic_where_in_template

select_results_for_shapefile_query = """
SELECT src_points.x, src_points.y, src_points.z, solutions.id, solutions.dip_dir, solutions.dip_ang, solutions.label, solutions.comments, solutions.creat_time
FROM solutions
INNER JOIN src_points
ON solutions.id = src_points.id_sol
"""

select_all_solutions_ids = """
SELECT id
FROM solutions
ORDER BY id ASC
"""

select_solution_pars_template = """
SELECT dip_dir, dip_ang, label, comments, creat_time
FROM solutions
WHERE id = {}
"""

select_sol_pts_pars_template = """
SELECT x, y, z
FROM src_points
WHERE id_sol = {}
ORDER BY id
"""
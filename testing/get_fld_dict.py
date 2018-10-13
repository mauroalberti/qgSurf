
flds = [
    {'id': {'name': 'id', 'type': 'INTEGER PRIMARY KEY'}},
    {'dip_dir': {'name': 'dip_dir', 'type': 'real'}},
    {'dip_ang': {'name': 'dip_ang', 'type': 'real'}},
    {'creat_time': {'name': 'creat_time', 'type': 'DATE'}},
    {'modif_time': {'name': 'modif_time', 'type': 'DATE'}}]


def get_field_dict(key_val, flds_dicts):

    filt_dicts = list(filter(lambda dct: key_val in dct.keys(), flds_dicts))

    if len(filt_dicts) == 1:
        return filt_dicts[0][key_val]
    else:
        return None


id_alias = get_field_dict('id', flds)
print(id_alias)


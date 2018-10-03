# -*- coding: utf-8 -*-


from typing import List, Tuple, Dict

from PyQt5.QtCore import QItemSelectionModel


def get_selected_recs_ids(selection_model: QItemSelectionModel) -> Tuple[int, ...]:
    """
    Get integer ids from selected records.

    :param selection_model: the selection model.
    :type selection_model: QItemSelectionModel.
    :return: the sequence of ids.
    :rtype: tuple of integers.
    """

    # get selected records attitudes

    selected_records = selection_model.selectedRows()

    if not selected_records:
        return ()

    selected_ids = tuple(map(lambda qmodel_ndx: qmodel_ndx.data(), selected_records))

    return selected_ids


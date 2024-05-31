#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import numpy as np

def logical_array_list_operation(list_in, operation):
    '''
    TODO
    '''
    assert isinstance(list_in, list)
    assert len(list_in) > 0
    assert operation in ['or', 'and']
    ar_loc = copy.deepcopy(list_in[0])
    for ii in range(1, len(list_in)):
        if operation == 'or':
            ar_loc = np.logical_or(ar_loc, list_in[ii])
        elif operation == 'and':
            ar_loc = np.logical_and(ar_loc, list_in[ii])
    return ar_loc

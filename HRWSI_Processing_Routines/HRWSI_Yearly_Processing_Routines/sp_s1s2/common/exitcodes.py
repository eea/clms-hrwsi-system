#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import traceback

##############
#exitcode handling

class ExitCodes:
    '''
    exitcode conventions:
    + 0 : success
    + 1 : unhandled errors (ideally not worth restarting over)
    + 2 : internal test error i.e. programming error => dev. team needed
    + codes in [10:50[ most likely CANNOT be solved by restarting job from scratch
    + codes in [50:100[ can very likely NOT be solved by restarting job from scratch but worth giving it a shot or make very minor tweaks to input parameters
    + codes in [100:200[ can likely be solved by restarting job from scratch. 129 to 192 correpond to unix kill signals 1 to 64.
    + codes in [200:255] are different exit states that are not errors (such as too high cloud cover for instance)

    common exitcodes:
    + 0 : success
    + 1 : this is for unhandled errors and is probably not solvable by restarting job (but you can maybe give it 1 shot)
    + 2 : not solvable : development team must debug this. program was probably not tested well enough before release. those are only the main anticipated programming errors but most will be unhandled and amount to exitcode=1
    + wrong_input_parameters : 10 #not solvable unless you change input parameters
    + main_input_file_error : 11 #may be solved by restarting job if there was a problem while copying input files
    + runtime_input_file_error : 12 #probably not solvable
    + subprocess_user_defined_timeout : 50 #may be solved by restarting job with larger limit on execution time allowed
    + dias_db_connexion_problem : 51 #not solvable unless DB or connexion was down for some reason
    + runtime_arg_error : 52 #runtime_arg_error
    + os_error : 100
    + disk_limit : 101
    + memory_limit : 102
    + 129 to 192 correpond to kill signals 1 to 64

    wic exitcodes:
    + maja_unknown_error : 110
    + wic_unknown_error = 111
    + maja_too_cloudy : 200
    + no_minilut_error : 201
    + l1c_fullnan : 202
    '''
    success = 0
    default = 1
    program_internal_test_error = 2

    wrong_input_parameters = 10
    main_input_file_error = 11
    runtime_input_file_error = 12

    subprocess_user_defined_timeout = 50 #may be solved by restarting job with larger limit on execution time allowed
    dias_db_connexion_problem = 51 #not solvable unless DB or connexion was down for some reason
    runtime_arg_error = 52 #runtime_arg_error

    os_error = 100
    disk_limit = 101
    memory_limit = 102

for ii in range(1, 64+1): #128+ii correpond to kill signals 1 to 64
    setattr(ExitCodes, f'kill_{ii}', 128+ii)

class CodedException(Exception):
    '''
    TODO
    '''
    def __init__(self, msg, exitcode=ExitCodes.default):
        super().__init__(msg)
        self.exitcode = exitcode
            
    def exit(self, print_traceback=True):
        '''
        TODO
        '''
        if print_traceback:
            _, exit_value, exit_traceback = sys.exc_info()
            full_msg = '\n'.join(['Traceback (most recent call last):'] + \
                [el.rstrip('\n') for el in traceback.format_tb(exit_traceback)] + \
                [exit_value.__repr__().split('(')[0] + f': {exit_value}'])
            print(full_msg)
        print(f'Exiting with code {self.exitcode}')
        sys.exit(self.exitcode)


class MainArgError(CodedException):
    """problem with input arguments that come from user defined parameters"""
    def __init__(self, msg):
        super().__init__(msg, exitcode=ExitCodes.wrong_input_parameters)
        
class InnerArgError(CodedException):
    """problem with input arguments that are due to internal program behaviour (should not exist)"""
    def __init__(self, msg):
        super().__init__(msg, exitcode=ExitCodes.program_internal_test_error)
        
class RuntimeArgError(CodedException):
    """problem with input arguments that may be due to wrong processing outputs but cannot be blamed to user or programmer"""
    def __init__(self, msg):
        super().__init__(msg, exitcode=ExitCodes.program_internal_test_error)

class MainInputFileError(CodedException):
    """file missing in main user-defined inputs"""
    def __init__(self, msg):
        super().__init__(msg, exitcode=ExitCodes.main_input_file_error)

class RuntimeInputFileError(CodedException):
    """file missing during execution"""
    def __init__(self, msg):
        super().__init__(msg, exitcode=ExitCodes.runtime_input_file_error)

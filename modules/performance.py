'''
The module 'performance' is used to analyse / measure
the performance of the minions, right from the master!
This module imports SysBench benchmark tool for
measuring various system parameters such as
CPU, Memory, FileI/O, Threads and Mutex.
#'''

import re
import salt.utils

__outputter__ = {'test':'txt',
                 'cpu':'txt',
                 'man':'txt'}


def man():
    '''
    Provides the help utility for using this module
    '''
    man_string = '''Usage:
    salt \* performance.man            - displays the help information
    salt \* performance.<test> run     - runs the test
    salt \* prrformance.<test> verbose - displays details of the test
    Available tests : cpu,mutex,threads,fileio,memory
    '''

    return man_string

def cpu(option):
    '''
    This tests for the cpu performance 
    of the minions
    Usage: salt '*' sysbench.cpu - executes the test
    '''
    
    # man option for cpu test
    if option == 'man':
        man_string = man_cpu()
        return man_string

    # values for test options (more values to be added)
    thread_values = [1]
    test_values = [5000]

    # patterns to be searched in output 
    time = r"( *total time: *[0-9]*s)"
    total_time = re.compile(time)
    per95 = r"( *approx. *95 percentile: *[0-9]*ms)"
    percentile = re.compile(per95)

    # return value (needs to be a dictionary)
    ret_val = None

    # the test begins
    for threads in thread_values:
        for primes in test_values:
            test_command = "sysbench --num-threads={0} --test=cpu --cpu-max-prime={1} run".format(threads,primes)
            ret_val = __salt__['cmd.run'](test_command)

            # code for extracting the required information should go here
            # should display the 95 percentile data for the user
    
    if option == 'verbose':
        return ret_val
    
    return None


def test():
 
    return True

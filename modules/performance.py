'''
The module 'performance' is used to analyse / measure
the performance of the minions, right from the master!
This module imports SysBench benchmark tool for
measuring various system parameters such as
CPU, Memory, FileI/O, Threads and Mutex.
'''

import re
import salt.utils

__outputter__ = {'test':'txt',
                 'cpu':'txt',
                 'threads':'txt',
                 'mutex':'txt',
                 'memory':'txt',
                 'fileio':'txt'}

def cpu():
    '''
    This tests for the cpu performance of minions. 
    In this test, the prime numbers are calculated
    upto the specified maximum limit. The total time 
    required to generate the primes is displayed in the 
    final result. Lower the time, better the performance!!
    USAGE: salt \* performance.cpu
    '''

    # maximum limits for prime numbers
    max_primes = [1000,5000] # 5000,10000,15000,20000 to be added

    # return values
    return_value = None
    result = '\nResult of sysbench.cpu test\n\n'

    # the test begins!
    for primes in max_primes:
        result = result + 'Maximum prime number={0}\n'.format(primes)
        test_command = "sysbench --test=cpu --cpu-max-prime={0} run".format(primes)
        return_value = __salt__['cmd.run'](test_command)
        result = result + return_value +'\n\n'

    return result

def threads():
    '''
    This tests the performance of the processor's
    scheduling. 
    USAGE: salt \* performance.threads
    '''

    # values for test option
    thread_yields = [100,500] #200, 500, 1000
    thread_locks = [2,16] #4,8,16

    # Initializing the required variables
    test_command = "sysbench --num-threads=64 --test=threads "
    return_value = None
    result = '\nResult of sysbench.threads test\n\n'
    
    # Testing yields!
    result = result + '\n\nStarting thread yield test\n'
    for yields in thread_yields:
        result = result + 'Number of yield loops={0}\n'.format(yields)
        run_command = (test_command+"--thread-yields={0} run").format(yields)
        return_value = __salt__['cmd.run'](run_command)
        result = result + return_value +'\n\n'

    # Testing for number of mutexs(locks) to create!
    result = result + '\n\nStarting thread lock test\n'
    for locks in thread_locks:
        result = result + 'Number of locks={0}\n'.format(locks)
        run_command = (test_command+"--thread-locks={0} run").format(locks)
        return_value = __salt__['cmd.run'](run_command)
        result = result + return_value +'\n\n'

    return result

def mutex():
    '''
    This test benchmarks the implementation of mutex.
    A lot of threads race for acquiring the lock
    over the mutex. However the period of acquisition
    is very short.
    USAGE: salt \* performance.mutex
    '''

    

def test():
 
    return True

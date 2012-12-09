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

def __virtual__():

    search_command = 'ls /usr/bin | grep sysbench'
    search_result = __salt__['cmd.run'](search_command)

    # if sysbench is not installed
    if search_result == None:
        return None

    # if sysbench is installed
    return 'sysbench'

def cpu(option):
    '''
    This tests for the cpu performance of minions. 
    In this test, the prime numbers are calculated
    upto the specified maximum limit. The total time 
    required to generate the primes is displayed in the 
    final result. Lower the time, better the performance!!
    USAGE: salt \* performance.cpu run - gives the total execution time
           salt \* performance.cpu verbose - gives a brief output
    '''

    if option not in ['run','verbose']:
        return 'Invalid argument as option'

    # maximum limits for prime numbers
    max_primes = [500,1000,5000] 

    # return values
    return_value = None
    result = '\nResult of sysbench.cpu test\n\n'

    # the test begins!
    for primes in max_primes:
        result = result + 'Maximum prime number={0}\n'.format(primes)
        test_command = "sysbench --test=cpu --cpu-max-prime={0} run".format(primes)
        return_value = __salt__['cmd.run'](test_command)
        if option == 'verbose':
            result = result + return_value
        elif option == 'run':
            time = re.search(r'total time:\s*\d.\d\d\d\ds',return_value)
            result = result + time.group() +'\n\n'

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

    # Test options and the values they take
    # --mutex-num = [50,500,1000]           
    # --mutex-locks = [10000,25000,50000]   
    # --mutex-loops = [2500,5000,10000]     

    # Orthogonal test cases
    mutex_num = [50,50,50,500,500,500,1000,1000,1000]
    mutex_locks = [10000,25000,50000,10000,25000,50000,10000,25000,50000]
    mutex_loops = [2500,5000,10000,10000,2500,5000,5000,10000,2500]

    # Initializing the required variables
    test_command = 'sysbench --num-threads=250 --test=mutex --mutex-num={0} --mutex-locks={1} --mutex-loops={2} run '
    return_value = None
    result = '\nResult of sysbench.mutex test\n\n'

    # The test begins here!
    for num,locks,loops in zip(mutex_num,mutex_locks,mutex_loops):
        result = result + '\nNumber of mutex={0}\nNumber of locks={1}\nNumber of loops={2}\n'.format(num,locks,loops)
        run_command = test_command.format(num,locks,loops)
        return_value = __salt__['cmd.run'](run_command)
        result = result + return_value

    return result

def memory():
    '''
    This tests the memory read and write operations.
    The threads can act either on their global or local
    memory space, depending on the option given. Other test 
    parameters like the block size and size of data to 
    be written / read are also specified in run command
    USAGE: salt \* performance.memory
    '''

    
 
def test():
 
    return True

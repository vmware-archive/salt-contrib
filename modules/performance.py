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
    max_primes = [500,1000,2500,5000] 

    # return values
    return_value = None
    result = '\nResult of sysbench.cpu test\n\n'

    # the test begins!
    for primes in max_primes:
        result = result + 'Maximum prime number={0}\n'.format(primes)
        test_command = "sysbench --test=cpu --cpu-max-prime={0} run".format(primes)
        return_value = __salt__['cmd.run'](test_command)
        if option == 'verbose':
            result = result + return_value +'\n\n'
        elif option == 'run':
            time = re.search(r'total time:\s*\d.\d*s',return_value)
            result = result + time.group() +'\n'

    return result

def threads(option):
    '''
    This tests the performance of the processor's
    scheduling. 
    USAGE: salt \* performance.threads run
           salt \* performance.threads verbose
    '''

    if option not in ['run','verbose']:
        return 'Invalid argument as option'    

    # values for test option
    thread_yields = [100,200,500,1000]
    thread_locks = [2,4,8,16] 

    # Initializing the required variables
    test_command = "sysbench --num-threads=64 --test=threads "
    return_value = None
    result = '\nResult of sysbench.threads test\n\n'
    
    # Testing begins!
    for yields,locks in zip(thread_yields,thread_locks):
        result = result + 'Number of yield loops={0}\n'.format(yields)
        result = result + 'Number of locks={0}\n'.format(locks)
        run_command = (test_command+"--thread-yields={0} --thread-locks={1} run").format(yields,locks)
        return_value = __salt__['cmd.run'](run_command)
        if option == 'verbose':
            result = result + return_value
        else:
            time = re.search(r'total time:\s*\d.\d*s',return_value)
            result = result + time.group() +'\n'

    return result

def mutex(option):
    '''
    This test benchmarks the implementation of mutex.
    A lot of threads race for acquiring the lock
    over the mutex. However the period of acquisition
    is very short.
    USAGE: salt \* performance.mutex run
           salt \* performance.mutex verbose
    '''

    if option not in ['run','verbose']:
        return 'Invalid argument as option'

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
        if option == 'verbose':
            result = result + return_value +'\n\n'
        else:
            time = re.search(r'total time:\s*\d.\d*s',return_value)
            result = result + time.group() +'\n'

    return result

def memory(option):
    '''
    This tests the memory read and write operations.
    The threads can act either on their global or local
    memory space, depending on the option given. Other test 
    parameters like the block size and size of data to 
    be written / read are also specified in run command
    USAGE: salt \* performance.memory run
           salt \* performance.memory verbose
    '''

    if option not in ['run','verbose']:
        return 'Invalid argument as option'

    # test defaults
    # --memory-block-size = 10M
    # --memory-total-size = 1G

    # We test memory read / write against global / local scope of memory
    memory_oper = ['read','write']
    memory_scope = ['local','global']

    # Initializing the required variables
    test_command = 'sysbench --num-threads=64 --test=memory --memory-oper={0} --memory-scope={1} --memory-block-size=1K --memory-total-size=1G run '
    return_value = None
    result = '''\nResult of sysbench.mutex test
    size  of memory block: 1K
    total size of data to transfer: 1G\n'''

    # Test begins!
    for oper in memory_oper:
        for scope in memory_scope:
            result = result + 'Operation:{0}\nScope:{1}'.format(oper,scope)
            run_command = test_command.format(oper,scope)
            return_value = __salt__['cmd.run'](run_command)
            if option == 'verbose':
                result = result + return_value +'\n\n'
            else:
                time = re.search(r'\s*total time:\s*\d.\d*s',return_value)
                result = result + time.group() +'\n\n'

    return result

def fileio(option):
    '''
    This tests for the file operations.
    Varients of file accesses are tested here.
    USAGE: salt \* performance.fileio run
           salt \* performance.fileio verbose
    '''

    if option not in ['run','verbose']:
        return 'Invalid option as argument'

    # Initializing the required variables
    test_command = 'sysbench --num-threads=16 --test=fileio --file-total-size=1M --file-test-mode={0} '
    return_value = None
    result = '\nResult of sysbench.fileio test\n\n'
    test_modes = ['seqwr','seqrewr','seqrd','rndrd','rndwr','rndrw'] 

    # Test begins!
    for mode in test_modes:
        result = result + 'mode:'+mode
        # Prepare phase
        run_command = (test_command + 'prepare').format(mode)
        __salt__['cmd.run'](run_command)
        # Test phase
        run_command = (test_command + 'run').format(mode)
        return_value = __salt__['cmd.run'](run_command)
        # Clean up phase
        run_command = (test_command + 'cleanup').format(mode)
        __salt__['cmd.run'](run_command)
        
        if option == 'verbose':
                result = result + return_value +'\n\n'
        else:
            time = re.search(r'\s*total time:\s*\d.\d*s',return_value)
            result = result + time.group() +'\n\n'
   
    return result

def test():
 
    return True

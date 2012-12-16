'''
The 'sysbench' module is used to analyse the
performance of the minions, right from the master!
It measures various system parameters such as
CPU, Memory, FileI/O, Threads and Mutex.
'''

import re
import salt.utils

__outputter__ = {
    'ping': 'txt',
    'cpu': 'txt',
    'threads': 'txt',
    'mutex': 'txt',
    'memory': 'txt',
    'fileio': 'txt'
}


def cpu(option='run'):
    '''
    Tests for the cpu performance of minions.

    CLI Examples::

        salt '*' sysbench.cpu
        salt '*' sysbench.cpu verbose
    '''

    if option not in ['run', 'verbose']:
        return 'Invalid option'

    # maximum limits for prime numbers
    max_primes = [500, 1000, 2500, 5000]

    # initializing the test command
    test_command = 'sysbench --test=cpu --cpu-max-prime={0} run'

    # return values
    return_value = None
    keys = ['run', 'verbose']
    ret_val = {key: '\nResult of sysbench.cpu test\n\n' for key in keys}

    # the test begins!
    for primes in max_primes:
        for key in ret_val.iterkeys():
            ret_val[key] += 'Maximum prime number={0}\n'.format(primes)
        run_command = test_command.format(primes)
        return_value = __salt__['cmd.run'](run_command)
        time = re.search(r'total time:\s*\d.\d*s', return_value)
        ret_val['verbose'] += return_value + '\n\n'
        ret_val['run'] += time.group() + '\n'

    if option == 'run':
        return ret_val['run']
    else:
        return ret_val['verbose']


def threads(option='run'):
    '''
    This tests the performance of the processor's scheduler

    CLI Example::

        salt \* sysbench.threads
        salt \* sysbench.threads verbose
    '''

    if option not in ['run', 'verbose']:
        return 'Invalid argument'

    # values for test option
    thread_yields = [100, 200, 500, 1000]
    thread_locks = [2, 4, 8, 16]

    # Initializing the required variables
    test_command = 'sysbench --num-threads=64 --test=threads '
    test_command += '--thread-yields={0} --thread-locks={1} run '
    return_value = None
    keys = ['run', 'verbose']
    ret_val = {key: '\nResult of sysbench.threads test\n\n' for key in keys}

    # Testing begins!
    for yields, locks in zip(thread_yields, thread_locks):
        for key in ret_val.iterkeys():
            ret_val[key] += 'Number of yield loops={0}\n'.format(yields)
            ret_val[key] += 'Number of locks={0}\n'.format(locks)
        run_command = test_command.format(yields, locks)
        return_value = __salt__['cmd.run'](run_command)
        time = re.search(r'total time:\s*\d.\d*s', return_value)
        ret_val['verbose'] += return_value + '\n\n'
        ret_val['run'] += time.group() + '\n'

    if option == 'run':
        return ret_val['run']
    else:
        return ret_val['verbose']


def mutex(option='run'):
    '''
    Tests the implementation of mutex

    CLI Examples::

        salt \* sysbench.mutex
        salt \* sysbench.mutex verbose
    '''

    if option not in ['run', 'verbose']:
        return 'Invalid argument'

    # Test options and the values they take
    # --mutex-num = [50,500,1000]
    # --mutex-locks = [10000,25000,50000]
    # --mutex-loops = [2500,5000,10000]

    # Orthogonal test cases
    mutex_num = [50, 50, 50, 500, 500, 500, 1000, 1000, 1000]
    locks = [10000, 25000, 50000, 10000, 25000, 50000, 10000, 25000, 50000]
    mutex_locks = []
    mutex_locks.extend(locks)
    mutex_loops = [2500, 5000, 10000, 10000, 2500, 5000, 5000, 10000, 2500]

    # Initializing the required variables
    test_command = 'sysbench --num-threads=250 --test=mutex '
    test_command += '--mutex-num={0} --mutex-locks={1} --mutex-loops={2} run '
    return_value = None
    iter_result = '\nNumber of mutex={0}\nNumber of locks={1}\n'
    iter_result += 'Number of loops={2}\n'
    keys = ['run', 'verbose']
    ret_val = {key: '\nResult of sysbench.mutex test\n\n' for key in keys}

    # The test begins here!
    for num, locks, loops in zip(mutex_num, mutex_locks, mutex_loops):
        for key in ret_val.iterkeys():
            ret_val[key] += iter_result.format(num, locks, loops)
        run_command = test_command.format(num, locks, loops)
        return_value = __salt__['cmd.run'](run_command)
        time = re.search(r'total time:\s*\d.\d*s', return_value)
        ret_val['verbose'] += return_value + '\n\n'
        ret_val['run'] += time.group() + '\n'

    if option == 'run':
        return ret_val['run']
    else:
        return ret_val['verbose']


def memory(option='run'):
    '''
    This tests the memory for read and write operations.

    CLI Examples::

        salt \* sysbench.memory
        salt \* sysbench.memory verbose
    '''

    if option not in ['run', 'verbose']:
        return 'Invalid argument'

    # test defaults
    # --memory-block-size = 10M
    # --memory-total-size = 1G

    # We test memory read / write against global / local scope of memory
    memory_oper = ['read', 'write']
    memory_scope = ['local', 'global']

    # Initializing the required variables
    test_command = 'sysbench --num-threads=64 --test=memory '
    test_command += '--memory-oper={0} --memory-scope={1} '
    test_command += '--memory-block-size=1K --memory-total-size=1G run '
    return_value = None
    keys = ['run', 'verbose']
    ret_val = {key: '''\nResult of sysbench.memory test\n\n
    size  of memory block: 1K
    total size of data to transfer: 1G\n''' for key in keys}

    # Test begins!
    for oper in memory_oper:
        for scope in memory_scope:
            for key in ret_val.iterkeys():
                ret_val[key] += 'Operation:{0}\nScope:{1}'.format(oper, scope)
            run_command = test_command.format(oper, scope)
            return_value = __salt__['cmd.run'](run_command)
            time = re.search(r'\s*total time:\s*\d.\d*s', return_value)
            ret_val['verbose'] += return_value + '\n\n'
            ret_val['run'] += time.group() + '\n'

    if option == 'run':
        return ret_val['run']
    else:
        return ret_val['verbose']


def fileio(option='run'):
    '''
    This tests for the file read and write operations

    CLI Examples::

        salt \* sysbench.fileio
        salt \* sysbench.fileio verbose
    '''

    if option not in ['run', 'verbose']:
        return 'Invalid option'

    # Initializing the required variables
    test_command = 'sysbench --num-threads=16 --test=fileio '
    test_command += '--file-total-size=1M --file-test-mode={0} '
    return_value = None
    keys = ['run', 'verbose']
    ret_val = {key: 'Result of sysbench.fileio test\n\n' for key in keys}
    test_modes = ['seqwr', 'seqrewr', 'seqrd', 'rndrd', 'rndwr', 'rndrw']

    # Test begins!
    for mode in test_modes:
        for key in ret_val.iterkeys():
            ret_val[key] += 'mode:{0}'.format(mode)
        # Prepare phase
        run_command = (test_command + 'prepare').format(mode)
        __salt__['cmd.run'](run_command)
        # Test phase
        run_command = (test_command + 'run').format(mode)
        return_value = __salt__['cmd.run'](run_command)
        time = re.search(r'\s*total time:\s*\d.\d*s', return_value)
        ret_val['verbose'] += return_value + '\n\n'
        ret_val['run'] += time.group() + '\n'
        # Clean up phase
        run_command = (test_command + 'cleanup').format(mode)
        __salt__['cmd.run'](run_command)

    if option == 'run':
        return ret_val['run']
    else:
        return ret_val['verbose']


def ping():

    return True

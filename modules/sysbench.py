'''
SysBench Module
This module faciliates the benchmarking of minions' performance
The following benchmark tests are provided by this module
  1. CPU
  2. Threads
  3. mutex
  4. memory
  5. fileio
'''

def __virtual__():
    '''
    This function verifies whether the SysBench package
    is installed in the minions or not
    '''

  
def cpu():
    '''
    This tests the performance of the CPU
    '''

    test_command = 'sysbench --test=cpu run'
    output = __salt__['cmd.run'](test_command)
    print output
    return

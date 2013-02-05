'''
Management of Keystone roles.
=============================

NOTE: This module requires the proper pillar values set. See
salt.modules.keystone for more information.

The keystone_role module is used to manage Keystone roles.

.. code-block:: yaml

    admin:
      keystone_role:
        - present
'''

def __virtual__():
    '''
    Only load if the keystone module is in __salt__
    '''
    return 'keystone_role' if 'keystone.role_create' in __salt__ else False

def present(name):
    '''
    Ensure that the named role is present

    name
        The name of the role to manage
    '''
    ret = {
            'name': name,
            'changes': {},
            'result': True,
            'comment': 'Role {0} is already presant'.format(name)
            }
    #Check if the tenant exists
    if not ('Error' in (__salt__['keystone.role_get'](name=name))):
        return ret

    #The tenant is not present, make it!
    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Role {0} is set to be added'.format(name)
        return ret
    if __salt__['keystone.role_create'](name):
        ret['comment'] = 'The role {0} has been added'.format(name)
        ret['changes'][name] = 'Present'
    else:
        ret['comment'] = 'Failed to create role {0}'.format(name)
        ret['result'] = False

    return ret

def absent(name):
    '''
    Ensure that the named role is absent

    name
        The name of the role to remove
    '''
    ret = {
            'name': name,
            'changes': {},
            'result': True,
            'comment': ''
            }

    #Check if tenant exists and remove it
    if not ('Error' in (__salt__['keystone.role_get'](name=name))):
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'Role {0} is set to be removed'.format(name)
            return ret
        if __salt__['keystone.role_delete'](name=name):
            ret['comment'] = 'Role {0} has been removed'.format(name)
            ret['changes'][name] = 'Absent'
            return ret
    #fallback
    ret['comment'] = (
            'Role {0} is not present, so it cannot be removed'
            ).format(name)
    return ret

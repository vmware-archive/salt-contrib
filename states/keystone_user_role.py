'''
Management of Keystone user-roles.
=============================

NOTE: This module requires the proper pillar values set. See
salt.modules.keystone for more information.

The keystone_user-role module is used to manage Keystone user-roles.

.. code-block:: yaml

    admin:
      keystone_user_role:
        - present
'''

def __virtual__():
    '''
    Only load if the keystone module is in __salt__
    '''
    return 'keystone_user_role' if 'keystone.user_role_add' in __salt__ else False

def present(name, role, tenant):
    '''
    Ensure that the named user role is present

    name
        The name of the user to manage
    role
        The name of the role to apply to the user
    tenant
        The name of the tenant 
    '''
    ret = {
            'name': name,
            'changes': {},
            'result': True,
            'comment': 'Role {0} is already presant on user {1}'.format(
                    role, 
                    name,
                    )
            }
    #Check if the user-role exists
    for role_item in __salt__['keystone.user_role_list'](
              user_name = name,
              tenant_name = tenant,
              ):
        if role_item == role:
            return ret

    #The tenant is not present, make it!
    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = (
                  'User {0} is set to have the role {1} added on {2}'
                  ).format(name, role, tenant)
        return ret
    if __salt__['keystone.user_role_add'](
              user_name = name,
              role_name = role,
              tenant_name = tenant,
              ):
        ret['comment'] = 'User {0} now has role {1} on {2}'.format(
                  name, role, tenant)
        ret['changes'][name] = 'Present'
    else:
        ret['comment'] = 'Failed to create User {0} role {1} on {2}'.format(
                  name, role, tenant)
        ret['result'] = False

    return ret

def absent(name, role, tenant):
    '''
    Ensure that the named role is absent

    name
        The name of the user to modify roles on
    role
        The role to remove from the user
    tenant
        The tenant to remove the users role from
    '''
    ret = {
            'name': name,
            'changes': {},
            'result': True,
            'comment': ''
            }

    #Check if role exists and remove it
    for role_item in __salt__['keystone.user_role_list'](
              user_name = name,
              tenant_name = tenant
              ):
        if role_item == role:
            if __opts__['test']:
                ret['result'] = None
                ret['comment'] = (
                          'User {0} role {1} is set to be removed from {2}'
                          ).format(name, role, tenant)
                return ret
                
            else:
                __salt__['keystone.user_role_remove'](
                      user_name = name,
                      role_name = role,
                      tenant_name = tenant,
                      )
                ret['comment'] = (
                          'User {0} has had role {1} removed from {2}'
                          ).format(name, role, tenant)
                ret['changes'][name] = 'Absent'
                return ret
    #fallback
    ret['comment'] = (
            'User {0}\'s role {1} is not present on {2}, so it cannot be \
            removed').format(name, role, tenant)
    return ret

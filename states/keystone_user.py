'''
Management of Keystone users.
=============================

NOTE: This module requires the proper pillar values set. See
salt.modules.keystone for more information.

The keystone_user module is used to manage Keystone users.

.. code-block:: yaml

    admin:
      keystone_user:
        - present
'''

def __virtual__():
    '''
    Only load if the keystone module is in __salt__
    '''
    return 'keystone_user' if 'keystone.user_create' in __salt__ else False

def present(name, password, email, tenant, enabled):
    '''
    Ensure that the named user is present

    name
        The name of the user to manage
    password
        The password the user should have
    email
        The email of the user
    tenant
        The name of the tenant the user should be associated with
    enabled
        Whether or not the user is enabled
    '''
    ret = {
            'name': name,
            'changes': {},
            'result': True,
            'comment': ('User {0} is already presant, ').format(name)
            }
    #Check if the user exists
    if ('Error' in (__salt__['keystone.user_get'](name=name))):
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'User {0} is set to be added.'.format(name)
        elif __salt__['keystone.user_create'](
                name, 
                password, 
                email, 
                tenant_id = __salt__['keystone.tenant_get'](
                        name=tenant)[tenant]['id'], 
                enabled=enabled):
            ret['comment'] = 'The user {0} has been added.'.format(name)
            ret['changes'][name] = 'Present'
        else:
            ret['comment'] = 'Failed to create user {0}'.format(name)
            ret['result'] = False
            return ret

    #Check the rest of the settings:
    if __salt__['keystone.user_get'](name=name)[name]['email'] != email:
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] += (
                    ' User {0} is set to have email updated to {1}.'
                    ).format(name, email)
        elif __salt__['keystone.user_update'](
                id = __salt__['keystone.user_get'](
                        name=name)[name]['id'],
                name = name,
                email = email,
                enabled = enabled,
                ):
            ret['comment'] += (
                    ' User {0} has had its email updated to {1}.'
                    ).format(name, email)
            ret['changes'][email] = 'Present'
        else:
            ret['comment'] = (
                    'Failed to update user {0}\'s email to {1}.'
                    ).format(name, email)
            ret['result'] = False
            return ret

    if __salt__['keystone.user_get'](name=name)[name]['enabled'] != enabled:
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] += (
                    ' User {0} is set to have status updated to {1}.'
                    ).format(name, enabled)
        elif __salt__['keystone.user_update'](
                id = __salt__['keystone.user_get'](name=name)[name]['id'],
                name = name, 
                email = email, 
                enabled = enabled,
                ):
            ret['comment'] += (
                    'The user {0} has had its status updated to {1}'
                    ).format(name, enabled)
            ret['changes'][enabled] = 'Present'
        else:
            ret['comment'] = (
                    'Failed to update user {0}\'s status to {1}'
                    ).format(name, enabled)
            ret['result'] = False
            return ret

    return ret

def absent(name):
    '''
    Ensure that the named user is absent

    name
        The name of the user to remove
    '''
    ret = {
            'name': name,
            'changes': {},
            'result': True,
            'comment': ''
            }

    #Check if user exists and remove it
    if not ('Error' in (__salt__['keystone.user_get'](name=name))):
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'User {0} is set to be removed'.format(name)
            return ret
        if __salt__['keystone.user_delete'](name=name):
            ret['comment'] = 'User {0} has been removed'.format(name)
            ret['changes'][name] = 'Absent'
            return ret
    #fallback
    ret['comment'] = (
            'User {0} is not present, so it cannot be removed'
            ).format(name)
    return ret

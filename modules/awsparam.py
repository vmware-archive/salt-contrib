# -*- coding: utf-8 -*-
'''Salt module that retrieves a key stored in Amazon's Parameter store.
Using this in a state file by setting a jinja variable allows the minion to retrieve secure strings directly from AWS
without having it stored on the salt master.

ie: {% set variable = salt['awsparam.get_parameter']('testkey') %} 
where testkey is the alias of you parameter store string

Requires boto3 to be installed on minion servers. 
https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-paramstore.html/
'''
import os
'''
Set variable on result of Library loading.
This will be used to either terminate the script or continue execution
'''
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False 

'''
Set AWS credentials here if you don't want them in the minion file
'''
AWS_CREDENTIALS = {
    "access_key": None,
    "secret_key": None,
}

def __virtual__():
    '''
    Load only if Boto3 succesfully imported
    '''
    return HAS_BOTO3
    
def _get_credentials ():
    '''
    Get AWS credentials:
        We need the credentials for a user that has Key User priveleges to the parameter password
        1) Hardcoded above in the AWS_CREDENTIALS dictionary.
        2) From the minion config file:
                    aws_keys:
                        access_key: ABC123
                        secret_key: abc123
    '''
    if AWS_CREDENTIALS["access_key"] and AWS_CREDENTIALS["secret_key"]:
        return AWS_CREDENTIALS
    try:
        aws_keys = __opts__.get("aws_keys", {})
        return {"access_key": aws_keys.get('access_key'),
                        "secret_key": aws_keys.get('secret_key'),}
    except (KeyError, NameError):
        return None
 
def _get_region ():
    '''
    Allow for region to be set in minion config
    Add a line like this: aws_region: eu-west-1
    '''
    aws_region = __opts__.get("aws_region")
    if aws_region:
        return aws_region
    else:
        return "eu-west-1"
 
def get_parameter (name):
    '''
    Get a parameter by name.
    '''
    region = _get_region ()
    credentials = _get_credentials ()
    
    ssm = boto3.client('ssm',region_name=region,aws_access_key_id=credentials["access_key"],aws_secret_access_key=credentials["secret_key"])
    try: 
        response = ssm.get_parameters(
                    Names=[
                            name,
                    ],
                    WithDecryption=True
            )
        parameter = response['Parameters'][0]['Value']
        return parameter

    except Exception:
        return

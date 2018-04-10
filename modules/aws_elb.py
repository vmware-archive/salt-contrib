#! /usr/bin/env python

import logging
import os

try:
    import boto
    has_boto = "aws_elb"
except ImportError:
    has_boto = False

LOG = logging.getLogger(__name__)
AWS_CREDENTIALS = {
    "access_key": None,
    "secret_key": None,
}


def __virtual__():
    """Don't load if boto is not available."""
    return has_boto


def _get_credentials():
    """
    Get AWS credentials:

      1) Hardcoded above in the AWS_CREDENTIALS dictionary.
      2) From the minion config ala:
          ec2_tags:
            aws:
              access_key: ABC123
              secret_key: abc123
      3) From the environment (AWS_ACCESS_KEY and AWS_SECRET_KEY).
      4) From the pillar (AWS_ACCESS_KEY and AWS_SECRET_KEY).

    """
    # 1. Get from static AWS_CREDENTIALS
    if AWS_CREDENTIALS["access_key"] and AWS_CREDENTIALS["secret_key"]:
        return AWS_CREDENTIALS
    try:  # 2. Get from minion config
        aws = __opts__.get["ec2_tags"]["aws"]
        return {"access_key": aws["access_key"],
                "secret_key": aws["secret_key"], }
    except (KeyError, NameError, TypeError):
        try:  # 3. Get from environment
            access_key = (os.environ.get("AWS_ACCESS_KEY")
                          or os.environ.get("AWS_ACCESS_KEY_ID"))
            secret_key = (os.environ.get("AWS_SECRET_KEY")
                          or os.environ.get("AWS_SECRET_ACCESS_KEY"))
            if access_key and secret_key:
                return {"access_key": access_key,
                        "secret_key": secret_key, }
            raise KeyError
        except (KeyError, NameError):
            try:  # 4. Get from pillar
                return {"access_key": __pillar__["AWS_ACCESS_KEY"],
                        "secret_key": __pillar__["AWS_SECRET_KEY"], }
            except (KeyError, NameError):
                LOG.error("No AWS credentials found.")
                return None


def _get_elb(name):
    """Get an ELB by name."""
    credentials = _get_credentials()
    if not credentials:
        return None
    conn = boto.connect_elb(credentials["access_key"], credentials["secret_key"])
    for lb in conn.get_all_load_balancers():
        if lb.name == name:
            return lb
    LOG.warning("Failed to find ELB: %s", name)
    return None


def join(name, instance_id=None):
    """
    Add instance to the given ELB.  Requires 'ec2_instance-id' to be
    given or be part of the minion's grains.

    CLI Example:

      salt '*' aws_elb.join MyLoadBalancer-Production

      salt '*' aws_elb.join MyLoadBalancer-Production i-89393af9

    """
    if instance_id is None:
        try:
            instance_id = __grains__["ec2_instance-id"]
        except KeyError:
            return False
    lb = _get_elb(name)
    try:
        lb.register_instances([instance_id, ])
    except Exception:
        import traceback
        LOG.error("ELB %s: Error while registering instance %s", name, instance_id)
        LOG.debug(traceback.format_exc())
        return False
    LOG.debug("ELB %s: Added instance %s", name, instance_id)
    return True


def leave(name, instance_id=None):
    """
    Removes instance from the given ELB.  Requires
    'ec2_instance-id' to be given or be part of the minion's grains.

    CLI Example:

      salt '*' aws_elb.leave MyLoadBalancer-Production

      salt '*' aws_elb.leave MyLoadBalancer-Production i-89393af9

    """
    if instance_id is None:
        try:
            instance_id = __grains__["ec2_instance-id"]
        except KeyError:
            return False
    lb = _get_elb(name)
    try:
        lb.deregister_instances([instance_id, ])
    except Exception:
        import traceback
        LOG.error("ELB %s: Error while deregistering instance %s", name, instance_id)
        LOG.debug(traceback.format_exc())
        return False
    LOG.debug("ELB %s: Removed instance %s", name, instance_id)
    return True


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    print _get_elb(sys.argv[1])

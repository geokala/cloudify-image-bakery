import os
import urllib2
from ConfigParser import ConfigParser

import boto.ec2
from cloudify import ctx
from cloudify_rest_client import CloudifyClient
from cloudify.state import ctx_parameters as inputs


BOTO_CONF = os.path.expanduser('~/.boto')


def get_manager_sg():
    url = 'http://169.254.169.254/latest/meta-data/security-groups'
    return urllib2.urlopen(url).read().split()[0]


def get_region():
    url = 'http://169.254.169.254/latest/meta-data/placement/availability-zone'
    return urllib2.urlopen(url).read()[:-1]


def create_boto_config(path, aws_access_key_id, aws_secret_access_key, region):
    config = ConfigParser()

    config.add_section('Credentials')
    config.set('Credentials',
               'aws_access_key_id',
               aws_access_key_id)
    config.set('Credentials',
               'aws_secret_access_key',
               aws_secret_access_key)

    config.add_section('Boto')
    config.set('Boto', 'ec2_region_name', region)

    ctx.logger.info('Saving boto config: {0}'.format(path))
    with open(path, 'w') as fh:
        config.write(fh)


def configure_security_groups(agents_sg_name):
    ctx.logger.info('Creating agent security group: {0}'
                    .format(agents_sg_name))

    conn = boto.ec2.EC2Connection()
    sg_desc = 'Security group for Cloudify agent VMs'
    sg = conn.create_security_group(agents_sg_name, sg_desc)
    manager_sg = conn.get_all_security_groups(groupnames=get_manager_sg())[0]
    ctx.logger.info('Manager group name: {0}'.format(manager_sg))

    # authorize from manager to agents
    add_tcp_allows_to_security_group(
        port_list=[22,5985],
        security_group=sg,
        from_group=manager_sg,
    )

    # authorize from agent to manager
    add_tcp_allows_to_security_group(
        port_list=[5672,8101,53229],
        security_group=manager_sg,
        from_group=sg,
    )

    return sg.id


def add_tcp_allows_to_security_group(port_list,
                                     security_group,
                                     from_group):
    for port in port_list:
        security_group.authorize('tcp', port, port, src_group=from_group)


def create_keypair(path, kp_name):
    ctx.logger.info('Creating keypair: {0}'.format(kp_name))
    conn = boto.ec2.EC2Connection()
    kp = conn.create_key_pair(kp_name)

    pk_path = os.path.join(path, kp.name + '.pem')
    ctx.logger.info('Saving keypair to: {0}'.format(pk_path))
    if not kp.save(path):
        raise RuntimeError('Failed saving keypair')

    return kp.name, pk_path


def update_context(agent_sg_id, agent_kp_id, agent_pk_path, agent_user):
    c = CloudifyClient()
    name = c.manager.get_context()['name']
    context = c.manager.get_context()['context']
    context['cloudify']['cloudify_agent']['agent_key_path'] = agent_pk_path
    context['cloudify']['cloudify_agent']['user'] = agent_user

    resources = {
        'agents_security_group': {
            'external_resource': False,
            'id': agent_sg_id
        },
        'agents_keypair': {
            'external_resource': False,
            'id': agent_kp_id
        }
    }
    context['resources'] = resources

    ctx.logger.info('Updating context')
    c.manager.update_context(name, context)


def main():
    create_boto_config(
        path=BOTO_CONF,
        aws_access_key_id=inputs['aws_access_key'],
        aws_secret_access_key=inputs['aws_secret_key'],
        region=get_region(),
    )

    sg_id = configure_security_groups(
        agents_sg_name=inputs['agents_security_group_name'],
    )
    akp_id, apk_path = create_keypair(path='~/.ssh/',
                                      kp_name=inputs['agents_keypair_name'])

    update_context(agent_sg_id=sg_id,
                   agent_kp_id=akp_id,
                   agent_pk_path=apk_path,
                   agent_user=inputs['agents_user'])

if __name__ == '__main__':
    main()

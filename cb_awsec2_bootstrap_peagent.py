"""
A Plugin that can install and configure the puppet agent if the Puppet Master
parameter is set. Requires the AWS EC2 user data field be empty.
Will not overwrite existing user data.

"""

import os
import sys
from utilities.logger import ThreadLogger

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append('/opt/cloudbolt')
logger = ThreadLogger(__name__)

aws_user_data = """#!/usr/bin/env bash

cat <<"EOPEREPO" > /etc/yum.repos.d/puppet_enterprise.repo
[puppet_enterprise]
name=PuppetLabs PE Packages $releasever - $basearch
baseurl=https://{{ server.puppet_master }}:8140/packages/current/el-$releasever-$basearch
enabled=1
gpgcheck=1
sslverify=0
gpgkey=https://{{ server.puppet_master }}:8140/packages/GPG-KEY-puppetlabs
       https://{{ server.puppet_master }}:8140/packages/GPG-KEY-puppet
EOPEREPO

/usr/bin/yum -y --disablerepo=\* --enablerepo=puppet_enterprise install puppet-agent

cat <<"EOPECONF" >> /etc/puppetlabs/puppet/puppet.conf
[main]
server = {{ server.puppet_master }}
[agent]
certname = {{ server.hostname }}
EOPECONF

/usr/bin/systemctl enable puppet
/usr/bin/systemctl start puppet
"""


def run(job, *args, **kwargs):
    cb_server = job.server_set.first()

    if cb_server.puppet_master:
        job.set_progress("When set, the Puppet Master parameter can use the "
                         "AWS EC2 'user data' field to automatically install "
                         "and configure the puppet agent. If the 'user data' "
                         "field already contains data, the puppet agent will "
                         "not be installed or configured automatically...")
        if cb_server.aws_user_data:
            job.set_progress("The AWS EC2 'user data' field already contains "
                             "data - Not installing or configuring the puppet "
                             "agent...")
        else:
            cb_server.aws_user_data = aws_user_data
            cb_server.save()
            job.set_progress("The AWS EC2 'user data' field has been set to "
                             "install and configure the puppet agent...")
    return "", "", ""

if __name__ == '__main__':
    job_id = sys.argv[1]
    from jobs.models import Job
    cb_job = Job.objects.get(id=job_id)
    print run(cb_job)

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import pexpect
import re
import subprocess
import socket
import datetime
import time

'''
    Here are only functions which is sudo controller 

    All Functions should be worked by itself
    and return result and err mesage

    functions naming 
        _name : internal functions
        name : normal functions

    usage)
        $ python remote.py [cmd] [args]

    [cmd]
        install 
            [args] : Docker_version, Docker_opts
        delete : 
        reconf : 
            [args] : Docker_opts
        restart : docker restart
        addhost : 
        start : flannel start
        stop : flannel stop
        makecert : change owner certification file 

    return : res[True,False], out[msg]
'''

def _validDockerProcess():
    time.sleep(2)
    mime = subprocess.Popen('/usr/bin/file /var/run/docker.sock', 
        shell=True, 
        stdout=subprocess.PIPE).communicate()[0]
    res = mime.split(' ')[1]

    if res == 'socket':
        return True
    else:
        return False

def _generateDockerConf(opts):
    # docker config generation
    now = datetime.datetime.now()
    tmp_docker_config = '/tmp/pose/docker.tmp'
    generated_opts = 'DOCKER_OPTS=\"${DOCKER_OPTS} ' + ' '.join(
        opts.split(',')) + ' \"'
        
    f = open(tmp_docker_config, 'w')
    f.write(generated_opts+'\n')
    f.close()

    cmd = 'sudo mv /etc/default/docker /etc/default/docker.old.'+\
        now.strftime('%H%M%S') + \
        '; sudo mv ' + \
        tmp_docker_config + ' /etc/default/docker'
    cmd_res = subprocess.call(cmd, shell=True)

    if cmd_res == 0:
        return True
    else:
        return False

def addHosts(host, ipaddr):

    try:
        # read a current hosts 
        f = open('/etc/hosts', 'r')
        org_hosts = f.readlines()
        f.close()
        f = open('/tmp/pose/hosts.tmp', 'w')

        for li in org_hosts:
            if re.search(ipaddr, li):
                f.close()
                os.system('rm /tmp/pose/hosts.tmp')

                return True, None
                sys.exit(0)
                
            f.write(li)
        
        f.write(ipaddr + '\t' + host + '\n')
        f.close()

        os.system('sudo cp /etc/hosts /etc/hosts.old')
        os.system('sudo cp /tmp/pose/hosts.tmp /etc/hosts')

        out = None
        
        return True, out

    except Exception as e:
        return False, e

def installDocker(path, filenm, opts):

    try :
        if filenm is None:
            raise NameError('remote.py:There a no Docker files')

        # install a docker daemon
        # add sudo apt-get install libltdl7 libsystemd-journal0
        # add sudo apt-get install linux-image-extra-$(uname -r)
        cmd = 'sudo dpkg -i ' + os.path.join(path, filenm)
        child = pexpect.spawn('/bin/bash', ['-c', cmd] )
        child.expect('[default=N] ?')
        child.sendline('N')
        child.expect(pexpect.EOF)

        # add a group for docker and a user 
        cmd = 'sudo groupadd docker; sudo gpasswd -a ${USER} docker'
        subprocess.check_output(cmd, shell=True)
        
        res, msg = restartDocker(opts, reconf=False)

        return True, None

    except Exception as e:
        return False, e
        
def deleteDocker():
    try:
        stop_cmd = 'sudo service docker stop'
        subprocess.call(stop_cmd, shell=True)

        cmd = 'sudo dpkg -P docker-engine'
        child = pexpect.spawn('/bin/bash', ['-c', cmd] )
        child.expect('[default=N] ?')
        child.sendline('N')
        child.expect(pexpect.EOF)
        #return True, "remove a docker Success"
        return True, None

    except Exception as e:
        return False, e


def restartDocker(opts, reconf=False):

    try:
        if reconf == True:
            if os.path.isfile('/run/flannel/subnet.env'):
                f = open('/run/flannel/subnet.env','r')
                flannel_opts = f.readlines()

            fsubnets = flannel_opts[1].split()[0].split("=")[1]
            fmtu = flannel_opts[2].split()[0].split("=")[1]
            
            add_opts = opts + ',--bip=' + fsubnets + ',--mtu=' + fmtu

            cmd = [ 'sudo ip links set dev docker0 down',
                'sudo brctl delbr docker0' ]

            for c in cmd:
                r = subprocess.call(c, shell=True)
                
                if not r:
                    raise NameError(
                        'remote.py:docker interface is NOT re-registryated')

            res = _generateDockerConf(add_opts)

            if not res: 
                raise NameError('remote.py:Reconfig docker is FAIL')

        else:
            res = _generateDockerConf(opts)

            if not res:
                raise NameError('remote.py:Reconfig docker is FAIL')

        restart_cmd = 'sudo service docker restart'
        restart_res = subprocess.call(restart_cmd, shell=True)
        
        res = _validDockerProcess()

        if not res:
            raise NameError('remote.py:Docker process is NOT working')

        return True, None

    except Exception as e:
        return False, e

def processController(compo, cmd):

    run_cmd = 'sudo service ' + compo + ' ' + cmd
    res = subprocess.call(run_cmd, shell=True)

    if res is False:
        raise NameError('remote.py:Your command is NOT working - %s' % run_cmd)

    return True, None

def makeCert():
   
    try: 
        cmd = 'sudo groupadd kube-cert'
        res = subprocess.call(cmd, shell=True)

        if res is False:
            raise NameError('remote.py:Fail to create group kube-cert')

        chg_cmd = 'sudo chgrp kube-cert /srv/kubernetes/server.key /srv/kubernetes/server.cert /srv/kubernetes/ca.crt'
        res = subprocess.call(chg_cmd, shell=True)
        
        if res is False:
            raise NameError('remote.py:Fail to change group kube-cert')

        chm_cmd = 'sudo chmod 660 /srv/kubernetes/server.key /srv/kubernetes/server.cert /srv/kubernetes/ca.crt'
        res = subprocess.call(chm_cmd, shell=True)

        if res is False:
            raise NameError('remote.py:Fail to change mod kube-cert')

        return True, None

    except Exception as e:
        return False, e


def usage():

    msg = 'Plz check the args using remote.py'
    res = False
    print '%s,%s' % (res, msg)
    sys.exit(1)

if __name__=='__main__':

    #IPADDR = socket.gethostbyname(socket.gethostname())
    HOST = socket.gethostname()

    if len(sys.argv) == 1:
        usage()

    if sys.argv[1] == 'install':

        if len(sys.argv) != 4:
            usage()
            
        VER = sys.argv[2]
        OPTS = sys.argv[3]
        BIN_PATH = '/tmp/pose'
        FILE_LIST = os.listdir(BIN_PATH)
        FILE = None

        for filenm in FILE_LIST:
            if re.search(VER, filenm):
                FILE=filenm

        res, msg = installDocker(BIN_PATH, FILE, OPTS)

    elif sys.argv[1] == 'delete':
        res, msg = deleteDocker()

    elif sys.argv[1] == 'reconf':

        if len(sys.argv) != 4:
            usage()

        OPTS = sys.argv[2]
        res, msg = restartDocker(OPTS, reconf=True)

    elif sys.argv[1] == 'restart':

        if len(sys.argv) != 4:
            usage()

        OPTS = sys.argv[2]
        res, msg = restartDocker(OPTS, reconf=False)

    elif sys.argv[1] == 'addhost':
        IPADDR = sys.argv[2]
        res, msg = addHosts(HOST, IPADDR)

    elif sys.argv[1] == 'start' or sys.argv[1] == 'stop':

        if len(sys.argv) != 3:
            usage()

        cmd = sys.argv[1]
        compo = sys.argv[2]
        res, msg = processController(compo, cmd)

    elif sys.argv[1] == 'makecert':
        res, msg = makeCert()

    else:
        usage()

    print '%s,%s' %(res, msg)

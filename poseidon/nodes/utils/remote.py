#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, pexpect, re, subprocess, socket, datetime, time

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

    return : res[True,False], out[msg]
'''

def _validDockerProcess():
    time.sleep(2)
    mime = subprocess.Popen('/usr/bin/file /var/run/docker.sock', shell=True, stdout=subprocess.PIPE).communicate()[0]
    res = mime.split(' ')[1]

    if res == 'socket':
        return True
    else:
        return False

def _generateDockerConf(opts):
    # docker config generation
    now = datetime.datetime.now()
    tmp_docker_config = '/tmp/pose/docker.tmp'
    generated_opts = 'DOCKER_OPTS=\"${DOCKER_OPTS} ' + ' '.join(opts.split(',')) + ' \"'
        
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
                return True, ipaddr + " already in hosts"
                sys.exit(0)
                
            f.write(li)
        
        f.write(ipaddr + '\t' + host + '\n')
        f.close()

        os.system('sudo cp /etc/hosts /etc/hosts.old')
        os.system('sudo cp /tmp/pose/hosts.tmp /etc/hosts')

        out = "To add a host is Success "
        
        return True, out

    except Exception as e:
        return False, e

def installDocker(path, filenm, opts):

    try :
        # install a docker daemon
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
        return True, "remove a docker Success"

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
                    raise NameError('docker interface is NOT re-registryated')

            res = _generateDockerConf(add_opts)

            if not res: 
                raise NameError('Reconfig docker is FAIL')

        else:
            res = _generateDockerConf(opts)

            if not res:
                raise NameError('Reconfig docker is FAIL')

        restart_cmd = 'sudo service docker restart'
        restart_res = subprocess.call(restart_cmd, shell=True)
        
        res = _validDockerProcess()

        if not res:
            raise NameError('Docker process is NOT working')

        return True, None

    except Exception as e:
        return False, e

def processController(cmd):
    run_cmd = 'sudo service flanneld ' + cmd
    res = subprocess.call(run_cmd, shell=True)

    if res is False:
        raise NameError('Your command is NOT working - %s' % run_cmd)

    return True, None

def configEtcd():
    pass

def usage():
    msg = 'Plz check the args using remote.py'
    res = False
    print '%s,%s' % (res, msg)
    sys.exit(1)

if __name__=='__main__':

    IPADDR = socket.gethostbyname(socket.gethostname())
    HOST = socket.gethostname()

    if len(sys.argv) == 1:
        usage()

    if sys.argv[1] == 'install':

        if len(sys.argv) < 4:
            usage()
            
        VER = sys.argv[2]
        OPTS = sys.argv[3]
        BIN_PATH = '/tmp/pose'
        FILE_LIST = os.listdir(BIN_PATH)

        for filenm in FILE_LIST:
            if re.search(VER, filenm):
                FILE=filenm

        res, msg = installDocker(BIN_PATH, FILE, OPTS)

    elif sys.argv[1] == 'delete':
        res, msg = deleteDocker()

    elif sys.argv[1] == 'reconf':

        if len(sys.argv) < 3:
            usage()

        OPTS = sys.argv[2]
        res, msg = restartDocker(OPTS, reconf=True)

    elif sys.argv[1] == 'restart':
        res, msg = restartDocker(reconf=False)

    elif sys.argv[1] == 'addhost':
        res, msg = addHosts(HOST, IPADDR)

    elif sys.argv[1] == 'start':
        cmd = 'start'
        res, msg = processController(cmd)

    elif sys.argv[1] == 'stop':
        cmd = 'stop'
        res, msg = processController(cmd)

    else:
        usage()

    print '%s,%s' %(res, msg)

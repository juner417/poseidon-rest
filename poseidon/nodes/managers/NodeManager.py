#-*- coding: utf-8 -*-
import datetime
import docker
import etcd
import json
import logging 
import os
import pexpect
import re
import sys
import urllib2
from nodes.models import Node
from clusters.models import Cluster
from components.models import Component

'''
class : NodeManager
role : Node init, install a kube binary

args : node_info(request.data)
{host, ipaddr, system_info(dict), role, component, cpu, mem, disk)

return : (True/False, if False then reason else None)
'''


class NodeManager(object):

    def __init__(self, data):
        # postfix : 's - array, _info - dictionary
        # data - serializer.data(orderd_dict) or node.object
    	self.logger = logging.getLogger(__name__)

        self.host = str(data['host'])
        self.ipaddr = str(data['ipaddr'])
        self.system_info = data['system_info']
        self.roles = [str(x) for x in data['roles']]
        self.component_info = data['component_info']
        self.acc = str(data['system_info']['account'])
        self.pubkey = str(data['system_info']['pubkey'])
        self.pemkey_path = str(data['system_info']['pemkey'])

        # create a binary dir
        if not os.path.isdir('/tmp/pose'):
            os.mkdir('/tmp/pose')

    def _connect_using_pexpect(self, target, cmd):
        # make a connection do something on remote host
        msg = 'Are you sure you want to continue connecting'
        child = pexpect.spawn('/bin/bash', ['-c', cmd], timeout=60)
        index = child.expect(
            [msg, 'password:', pexpect.EOF, pexpect.TIMEOUT])

        try:
            if index == 0 :
                child.sendline('yes')
                index = child.expect(
                    [msg, 'password:', pexpect.EOF, pexpect.TIMEOUT])

            if index == 1:
                self.logger.debug(
                    '%s server is require passwd to login ' % \
                    (target))
                child.close(force=True)
                res = False
                out = "password required"

            elif index == 2:
                if child.before == '' or re.search('100%', child.before):
                    res = True
                    out = None
                else:
                    #self.logger.debug(child.before)
                    remote_res = str(child.before.split('\r\n')[-2])
                    tmp_arr = remote_res.split(',')
                    
                    if tmp_arr[0] == 'True':
                        res = bool(1)
                    else:
                        res = bool(0)
                    out = tmp_arr[1]

                if res is False: 
                    self.logger.debug('cmd: %s' % cmd)
                self.logger.debug(
                    'node: %s res: %s out: %s' % (target, res, out))

            else:
                self.logger.error('cannot connect to %s' % target)
                res = False
                out = "cannot connect"

            if res is True:
                return True, out
            else:
                raise NameError(res, out)

        except Exception as e:
            return False, e

    def _call_api(self, url=None, body=None, method='GET'):
        
        if url is None:
            raise NameError('url is None')

        opener = urllib2.build_opener(urllib2.HTTPHandler)
        req = urllib2.Request(url, body)
        req.add_header('Content-Type', 'application/json')
        req.get_method = lambda: method
        res = urllib2.urlopen(req)
        res.close()

        if res.code == 200:
            return True, None
        else:
            err = 'url: %s, res: %s-%s ' % (res.url, res.code, res.msg)
            return False, res.code+'-'+res.msg

    def initNode(self, file=None):
        # deploy ssh key and hosts
        self.logger.debug('initiate a node(%s)' % self.host)
        f = open(os.path.join('/tmp/pose', 'authorized_keys.tmp'), 'w')
        f.write(self.pubkey + '\n')
        f.close()
        os.chmod('/tmp/pose/authorized_keys.tmp', 0755)

        if file is None:
            file = '/tmp/pose/'

        # deploy pub key
        run_cmd = 'scp -i ' + self.pemkey_path + \
                  ' /tmp/pose/authorized_keys.tmp ' + \
                  self.acc + '@' + self.ipaddr + ':/tmp/'

        # copy a pub key
        cmd = \
            'ssh -i ' + self.pemkey_path + \
            ' ' + self.acc + '@' + self.ipaddr + \
            ' \' cat ~/.ssh/authorized_keys | grep \"' + \
            self.pubkey[:80] + '\"' + \
            ' 1> /dev/null 2>&1 || cat /tmp/authorized_keys.tmp >> ~/.ssh/authorized_keys \' '

        # add hosts
        copycmd = 'scp -i ' + self.pemkey_path + ' -r ' + \
            file + ' ' + self.acc + '@' + self.ipaddr + ':/tmp/'
        instcmd = 'ssh -i ' + self.pemkey_path + ' ' + \
            self.acc + '@' + self.ipaddr + \
            ' \" sudo apt-get install python-pexpect; python /tmp/pose/remote.py addhost ' + \
            self.ipaddr + '\"'

        try: 
            res, err = self._connect_using_pexpect(self.host, run_cmd)

            if res is False:
                raise NameError('Fail to copy pubkey at %s (%s)' % self.host, err)

            cres, err = self._connect_using_pexpect(self.host, cmd)

            if cres is False:
                raise NameError('Fail to deploy pubkey at %s (%s)' % self.host, err)

            cres = False
            ires = False
            i = 0
            
            while i < 5:
                if cres is False:
                    cres, cout = self._connect_using_pexpect(
                        self.host, copycmd)

                if cres is True:
                    ires, err = self._connect_using_pexpect(
                        self.host, instcmd)

                    if ires is True:
                        i = 100

                i+=1

            # verify and return 
            if cres is True and ires is True:
                return True, None
            else:
                if cres is False:
                    err = cout

                return False, err

        except Exception as e:
            return False, e
            self.logger.error(e)

    def installDocker(self, opts, file=None):
        # install docker bin
        # options pull a kube-box image
        self.logger.debug('Docker is now install on node(%s)' % self.host)

        if file is None:
            file = '/tmp/pose/'
       
        docker_opts = ','.join(opts)
        copycmd = \
            'scp -i ' + self.pemkey_path + ' -r ' + file + \
            ' ' + self.acc + '@' + self.ipaddr + ':/tmp/'
        instcmd = \
            'ssh -i ' + self.pemkey_path + ' ' + \
            self.acc + '@' + self.ipaddr + \
            ' \" sudo apt-get install python-pexpect; python /tmp/pose/remote.py install ' + \
            self.component_info['docker'] + ' ' + \
            docker_opts + ' \"'

        try: 

            cres = False
            res = False
            
            while cres == False:
                cres, cout = self._connect_using_pexpect(
                    self.host, copycmd)
                if cres == True:
                    res, err = self._connect_using_pexpect(
                        self.host, instcmd)
            
            # verify and return 
            if cres is True and res is True:
                return True, None
            else:
                if not cres:
                    err = cout

                return False, err

        except Exception as e:
            self.logger.error(e)

    def startNode(self):

        if 'meta' in self.roles:
            startcmd = 'ssh -i ' \
                + self.pemkey_path + ' ' \
                + self.acc + '@' + self.ipaddr + \
                ' \" python /tmp/pose/remote.py start etcd \" ' 

            res, out = self._connect_using_pexpect(self.host, startcmd)

            if res is False:
                return False, out

        startcmd = 'ssh -i ' \
            + self.pemkey_path + ' ' \
            + self.acc + '@' + self.ipaddr + \
            ' \" python /tmp/pose/remote.py start flanneld \" ' 

        res, out = self._connect_using_pexpect(self.host, startcmd)

        if res is False:
            return False, out

        return res, None

    def stopNode(self, file=None):

        if file is None:
            file = '/tmp/pose/'

        copycmd = \
            'scp -i ' + self.pemkey_path + ' -r ' + \
            file + ' ' + self.acc + '@' + self.ipaddr + ':/tmp/'
        flannelcmd = \
            'ssh -i ' + self.pemkey_path + ' ' + \
            self.acc + '@' + self.ipaddr + \
            ' \" python /tmp/pose/remote.py stop flanneld \" ' 
        etcdcmd = \
            'ssh -i ' + self.pemkey_path + ' ' + \
            self.acc + '@' + self.ipaddr + \
            ' \" python /tmp/pose/remote.py stop etcd \" ' 

        cres = False
        res = False

        try:
            i = 0
            
            while i < 5:
                cres, cout = self._connect_using_pexpect(
                    self.host, copycmd)

                if cres == True:
                    res, err = self._connect_using_pexpect(
                        self.host, flannelcmd)

                    # for stoping etcd 
                    if res is True and 'master' in self.roles:
                        res, err = self._connect_using_pexpect(
                            self.host, etcdcmd)

                    if res is True:
                        i = 100

                i+=1
           
            # verify and return 
            if cres is True and res is True:
                return True, None
            else:
                if not cout:
                    err = cout

                return False, err

        except Exception as e:
            self.logger.error(e)

    def launchBox(self, cluster, components):
        #launch poseidon box
        #cluster(model), components(model, array)
        now = datetime.datetime.now()
        roles = ','.join(self.roles)
        metas = [str(x) for x in cluster.metas]
        box_ver = str(cluster.platform_info['box_version'])
        box_image = str(cluster.platform_info['registry']) + '/poseidon-box'
        etcd_peer = 'http://' + ',http://'.join(metas)
        cluster_api = str(cluster.master) + ':' + str(cluster.port)
        container_env = []

        self.logger.debug('Launching poseidon-box on node(%s)' % self.host)

        for c in components:
            generated_opts = ''
            for k, v in c.opts.items():
                if str(v) == "FLAG":
                    generated_opts += ' %s' %(str(k))
                elif str(v) == "HOST":
                    generated_opts += ' %s=%s' %(str(k), self.host)
                elif str(v) == "IP":
                    generated_opts += ' %s=%s' %(str(k), self.ipaddr)
                else:
                    generated_opts += ' %s=%s' %(str(k), str(v))
                
            if c.name == 'kubelet':
                kubelet_opt = generated_opts
            elif c.name == 'kube-proxy':
                kubeproxy_opt = generated_opts
            elif c.name == 'flanneld':
                flanneld_opt = generated_opts
            elif c.name == 'kube-apiserver':
                kubeapi_opt = generated_opts
            elif c.name == 'kube-scheduler':
                kubesched_opt = generated_opts
            elif c.name == 'kube-controller-manager':
                kubecont_opt = generated_opts
            elif c.name == 'etcd':
                etcd_opt = generated_opts
            else:
                # maybe add a docker conf
                pass

        for r in self.roles:
            if r == 'master': 
                container_env.append(
                    'KUBE_APISERVER_OPTS='+kubeapi_opt)
                container_env.append(
                    'KUBE_SCHEDULER_OPTS='+kubesched_opt)
                container_env.append(
                    'KUBE_CONTROLLER_MANAGER_OPTS='+kubecont_opt)
            elif r == 'minion':
                container_env.append('KUBELET_OPTS='+kubelet_opt)
                container_env.append('KUBE_PROXY_OPTS='+kubeproxy_opt)
                container_env.append('FLANNELD_OPTS='+flanneld_opt)
            elif r == 'meta':
                container_env.append('ETCD_OPTS='+etcd_opt)

        container_env.append('SYNCOPTS=replace')
        container_env.append('CMD=install')
        container_env.append('ROLES='+roles)

        try:
            c = docker.Client(
                version='1.21', 
                base_url='http://'+self.ipaddr+':4243')
            c.pull(repository=box_image, tag=box_ver)

            container_id = c.create_container(
                image=box_image + ':' + box_ver,
                volumes=['/opt/bin', '/etc/default', 
                    '/etc/init.d', '/etc/init/', 
                    '/srv/kubernetes'], 
                name='poseidon-box-install-' + now.strftime('%H%M%S'),
                environment=container_env
            )

            res = c.start(
                container_id,
                binds = {
                    '/opt/bin':{
                        'bind':'/mnt/opt/bin', 
                        'ro':False}, 
                    '/etc/default':{
                        'bind':'/mnt/etc/default', 
                        'ro':False},
                    '/etc/init.d':{
                        'bind':'/mnt/etc/init.d', 
                        'ro':False},
                    '/etc/init':{
                        'bind':'/mnt/etc/init', 
                        'ro':False},
                    '/srv/kubernetes':{
                        'bind':'/mnt/srv/kubernetes', 
                        'ro':False}
                }
            )

            res = c.inspect_container(container_id)['State']['ExitCode']

            if res != 0:
                self.logger.debub()
                raise NameError('Fail to launch poseidon-box(exitcode:%s)' % res)

            # change owner kube-cert files
            if 'master' in self.roles:
                # change owner kube-cert file
                cmd = \
                    'ssh -i ' + self.pemkey_path + ' ' + \
                    self.acc + '@' + self.ipaddr + \
                    ' \" python /tmp/pose/remote.py makecert \" ' 

                res, err = self._connect_using_pexpect(
                    self.host, cmd)

                if res is False:
                    return False, err
            
            return True, res

        except Exception as e:
            return False, e

    def reConfDocker(self, opts, cluster):
        '''
        1. reconf docker after launchbox
        2. if roles have a master then set a etcd
        '''
        roles = self.roles
        docker_opts = ','.join(opts)

        for r in roles:

            #self.logger.debug('role : %s' % r)
            if r == 'master':
                # verify key /coreos.com/network/config
                # if not key create key /coreos.com/network/config
                metas = [(str(x).split(':')[0], str(x).split(':')[1]) for x in cluster.metas]
                etcd_values = \
                    '{\"Network\":\"' + \
                    str(cluster.network_info['Network']) + \
                    '\", ' + \
                    '\"Backend\":{\"Type\":\"' + \
                    cluster.network_info['Backend']['Type'] + \
                    '\"} }'

                if len(metas) == 1:
                    etcd_client = etcd.Client(
                        host=metas[0][0], port=int(metas[0][1]))
                else:
                    etcd_client = etcd.Client(
                        tuple(metas), allow_reconnect=True)

                try:
                    etcd_client.read('/coreos.com/network/config')
                    self.logger.info(
                        'etcd %s has a network config key' % \
                        self.host)
                    res = True

                except etcd.EtcdKeyNotFound:
                    self.logger.info(
                        'etcd %s has not a network config key, so now create it' % \
                        self.host)
                    val = etcd_client.write(
                        '/coreos.com/network/config', etcd_values)

                    if val: 
                        res = True
                    else:
                        res = False
                        out = 'creating a etcd key is Fail'

            elif r == 'minion':
                cmd = \
                    'ssh -i ' + self.pemkey_path + ' ' + self.acc + \
                    '@' + self.ipaddr + \
                    ' \"python /tmp/pose/remote.py reconf ' + \
                    docker_opts + ' ' + r + ' \" '

                res, out = self._connect_using_pexpect(self.host, cmd)

            elif r == 'meta':
                pass

            if res is False:
                return False, out

        return True, None

    def unInstallNode(self, cluster):
        '''
        1.uninstall a kubernetes and docker in node
        2.kube binary delete(kube-proxy, kubelet, kube-api...)
        '''
        now = datetime.datetime.now()
        roles = ','.join(self.roles)
        box_ver = str(cluster.platform_info['box_version'])
        box_image = str(cluster.platform_info['registry']) + \
            '/poseidon-box'

        container_env = []
        container_env.append('SYNCOPTS=replace')
        container_env.append('CMD=uninstall')
        container_env.append('ROLES='+roles)

        try: 
            c = docker.Client(
                version='1.21', 
                base_url='http://'+self.ipaddr+':4243')
            c.pull(repository=box_image, tag=box_ver)

            container_id = c.create_container(
                image=box_image + ':' + box_ver,
                volumes=['/opt/bin', '/etc/default', 
                    '/etc/init.d', '/etc/init/', 
                    '/srv/kubernetes'], 
                name='poseidon-box-uninstall-'+now.strftime('%H%M%S'),
                environment=container_env
            )

            res = c.start(
                container_id,
                binds = {
                    '/opt/bin':{
                        'bind':'/mnt/opt/bin', 
                        'ro':False}, 
                    '/etc/default':{
                        'bind':'/mnt/etc/default', 
                        'ro':False},
                    '/etc/init.d':{
                        'bind':'/mnt/etc/init.d', 
                        'ro':False},
                    '/etc/init':{
                        'bind':'/mnt/etc/init', 
                        'ro':False},
                    '/srv/kubernetes':{
                        'bind':'/mnt/srv/kubernetes', 
                        'ro':False}
                }
            )

            res = c.inspect_container(container_id)['State']['ExitCode']

            if res != 0:
                self.logger.debub()
                raise NameError('Fail to launch poseidon-box(exitcode:%s)' % res)

            return True, None

        except Exception as e:
            return False, e

    def removeNode(self, cluster):
        '''
        1. purge docker
           -- using util/remote.py delete
        2. delete etcd(/coreos.com/network/subnets/${node_subnets})
        3. delete kubernetes node 
        '''
        try:
            metas = [(str(x).split(':')[0], int(str(x).split(':')[1])) for x in cluster.metas]

            # purge docker daemon
            startcmd = \
                'ssh -i ' + self.pemkey_path + ' ' + \
                self.acc + '@' + self.ipaddr + \
                ' \" python /tmp/pose/remote.py delete \" ' 

            res, out = self._connect_using_pexpect(self.host, startcmd)
           
            if res is False:
                raise NameError('Fail to delete docker daemon(%s)' % self.host)

            if 'minion' in self.roles:
                # find a deleted node info in etcd meta (key=self.ipaddr)
                if len(metas) == 1:
                    etcd_client = etcd.Client(
                        host=metas[0][0], port=int(metas[0][1]))
                else:
                    etcd_client = etcd.Client(
                        tuple(metas), allow_reconnect=True)

                subnet_list = etcd_client.read(
                    '/coreos.com/network/subnets', recursive=True)
                
                key = None
                for i in range(0, len(subnet_list._children)):
                    ip = str(json.loads(
                            str(subnet_list._children[i]['value'])
                        )['PublicIP'])

                    if ip == self.ipaddr:
                        key = str(subnet_list._children[i]['key'])
                        self.logger.debug('Find a key : %s' % key)

                if key is None:
                    self.logger.debug(
                        'There\'s no %s in etcd meta' % self.ipaddr)
                else:
                    self.logger.debug(
                        'Delete a %s in etcd meta' % self.ipaddr)
                    etcd_client.delete(key)


                # delete node info in kubernetes
                api_url = 'http://' + cluster.master + ':' + cluster.port + '/api/v1/nodes/'
                try: 
                    node_url = api_url + self.host
                    api_info = urllib2.urlopen(node_url).read()
                except urllib2.HTTPError as ue:
                    node_url = api_url + self.ipaddr

                res, out = self._call_api(node_url, None, 'DELETE')

                if res is True:
                    return True, None
                else:
                    err = '%s' % (out)
                    return False, err

            return res, None

        except Exception as e:
            self.logger.error('%s' %e)
            return False, e

    def is_valid(self):
        # kube-apiserver에서 node 등록 및 상태가 정상인지 확인
        return True

    def rollback(self):
        # rollback process
        pass

    def display(self):
        pass

    def __unicode__(self):
        return self.host
        

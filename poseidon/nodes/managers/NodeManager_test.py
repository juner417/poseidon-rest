#!/usr/bin/python
#-*- coding: utf-8 -*-
import time, os, sys, json, ast
from restapi.models import Node, Cluster, Component
from restapi.serializers import NodeSerializer, ClusterSerializer, ComponentSerializer
from django.http import Http404, HttpResponse, JsonResponse
from NodeManager import NodeManager

def run_test():
    node = {
    "host": "k8s-nminion-05",
    "ipaddr": "172.19.136.203",
    "system_info": { 
    	"os": "ubuntu-14.04", 
    	"account" : "ubuntu", 
    	"pubkey" : "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDkyjBMFzm2TViVZlgK6AS1bONpsVH7iG5ngksVZmWdA0p50koCkRxkVaECVa+exB6rb7jxCOt6Qskw0uDO3pyOiPEk21rJJHRsQqmdTG3erD+DuWNwnxtXuGmK9AJzMoE1bwb9qaMfePdqMYK42WaV+kk9X1wflNuPK40No4PrMd0fzRErnaoHoAbUfcpV3JkUEgiboH6Pd2y4Cozm9vi+Mg2bmrcBY7C7Qd59zZJHZDyTBcw04dZ7otkZk37X2Ghg8M4dYQ77OXed/C2vMeojlno7mCf0T18Wdn14/5ug9JvlTqgj7Qo8lxxPBNvPu+pwivPJVnZbE5CmRZV5gybz ubuntu@ncsoft.com",
    	"pemkey" : "/Users/junerson/dev/.keys/kubernetes.pem"
    },
    "role" : ["node"],
    "component_info" : {
    	"kubelet":"v1.5.2", 
    	"kube-proxy": "v1.5.2", 
    	"flanneld":"0.5.5", 
        "docker" : "1.12.3"},
    "cluster" : "cluster-5c15f70a",
    "cpu": 16,
    "mem": 24,
    "disk": 100, 
    "tags": {
    	"test": "test1"
    },
    "status" : "False" }

    node_info = { "uuid" : "node-20456ca1" }
    
    # transfer a json
    #node_info_json = json.dumps(node)
    #serializer = NodeSerializer(data=node)
    node = Node.objects.get(uuid=node_info['uuid'])
    print(node)
    serializer = NodeSerializer(node)
    
    #if serializer.is_valid():
        #print("validated data : %s" % serializer.validated_data)
    #print(serializer.validated_data)
    #print(serializer.data)
    node_manager = NodeManager(serializer.data)
    cluster_obj = node.cluster
    component_obj = Component.objects.all().filter(cluster=str(node.cluster.uuid))
    registries = [ str(x) for x in cluster_obj.platform_info['registry']]
    res = node_manager.initNode()

    if not res:
        print("ERROR) initNode()")
        sys.exit(1)

    res = node_manager.installDocker(registries)

    if not res:
        print("ERROR) installDocker()")
    
    res = node_manager.launchBox(cluster_obj, component_obj)
    time.sleep(4)
    node_manager.startNode()
    time.sleep(1)
    node_manager.reConfDocker(registries)

    #else:
    #    print("not valid")
    #    print(serializer.data)

if __name__=='__main__':
    run_test()

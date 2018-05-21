# -*- coding: utf-8 -*-
import ast
import json
import logging
import os
import sys
import time
from nodes.models import Node
from clusters.models import Cluster
from components.models import Component
from managers.NodeManager import NodeManager
from nodes.serializers import NodeSerializer
from clusters.serializers import ClusterSerializer
from components.serializers import ComponentSerializer
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, api_view
from rest_framework import status, permissions, schemas

@permission_classes((permissions.AllowAny,))
class NodeJoinViewer(APIView):

    def __init__(self):
        APIView.__init__(self)
        self.logger = logging.getLogger(__name__)

    def get(self, request, cluster_uuid, node_uuid=None, format=None):
        """ cluster_uuid에 속한 node 목록 확인 """

        cluster = Cluster.objects.get(uuid=cluster_uuid)

        if node_uuid is None:
            nodes = Node.objects.filter(
                cluster=cluster_uuid)
        else:
        # components have many entities
            nodes = Node.objects.filter(
                cluster=cluster_uuid,
                uuid=node_uuid)

        serializer = NodeSerializer(nodes, many=True)

        return Response(serializer.data)

@permission_classes((permissions.AllowAny,))
class NodeController(APIView):
    
    def _change_status_failure(self, model):
        status = {'status' : 'fail'}
        serializer.update(model, status)

    def get(self, request, uuid, format=None):
        pass

    def post(self, request, uuid=None, format=None):
        pass

    def put(self, request, uuid, format=None):
        """ node status 변경 
        ---
        serializer: 
            - NodeSerializer

        parameters:
            - name: uuid
              description: node uuid
              type: string

            - name: status
              description: node status
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """ 

        # node status = [plain|running|disturbed|unscheduled|eliminated]
        msg = {}
        action_status_ref = [
            'install', 
            'sync', 
            'drain', 
            'uninstall', 
            'plain'
        ]
        node_status_ref = [
            'running',
            'disturbed',
            'unscheduled',
            'eliminated'
        ] 

        node = Node.objects.get(uuid=request.data['uuid'])
        serializer = NodeSerializer(node)

        # get the cluster, component models for cluster_info, component_info
        cluster = node.cluster
        components = Component.objects.all().filter(
            cluster=str(node.cluster.uuid))
        cur_node_stat = node.status
        next_node_stat = request.data['status']

        assert request.data['status'] in action_status_ref, (
            'Node status action is only has follow values %s' % (
                ','.join(x for x in node_status_ref))
        )

        if request.data['uuid'] != uuid:
            msg['message'] = \
                'The difference node_id between requests and resource url'
            return Response(data=msg, 
                status=status.HTTP_406_NOT_ACCEPTABLE)

        if next_node_stat == 'install':
        
            if str(node.status) != 'plain':
                msg['message'] = \
                    'a Node status is not suitable to install binary'
                return Response(data=msg, 
                    status=status.HTTP_406_NOT_ACCEPTABLE)

            if str(node.status) == 'running':
                msg['message'] = \
                    'a Node status is now running'
                return Response(data=msg, 
                    status=status.HTTP_406_NOT_ACCEPTABLE)

            # docker component opts are only using "--" flag
            opts = []
            for k, v in components.get(name='docker').opts.items():

                if type(v) is list:

                    values = [ str(x) for x in v ]
                    for list_v in values:
                        opts.append(str(k) + '=' + str(list_v))

                else:
                    opts.append(str(k) + '=' + str(v))

            # create nodeManager
            node_manager = NodeManager(serializer.data)

            res, out = node_manager.initNode()

            if res is not True:
                msg['message'] = \
                    '%s initiation is Fail(reason:%s)' % \
                    (node.host, out)
                return Response(data=msg, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # docker install    
            res, out = node_manager.installDocker(opts)

            if res is not True:
                msg['message'] = \
                    '%s Docker installation is Fail(reason:%s)' % \
                    (node.host, out)
                return Response(data=msg, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # launch a poseidon-box
            res, out = node_manager.launchBox(cluster,components)

            if res is not True:
                msg['message'] = \
                    '%s launch a poseidon-box(install) is Fail(reason:%s)' % \
                    (node.host, out)
                return Response(data=msg, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            time.sleep(3)
            res, out = node_manager.startNode()
            
            if res is not True:
                msg['message'] = \
                    '%s node restart is Fail(reason:%s)' % \
                    (node.host, out)
                return Response(data=msg, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            time.sleep(1)
            res, out = node_manager.reConfDocker(opts, cluster)

            if res is not True:
                msg['message'] = \
                    '%s reconfdocker is Fail(reason:%s)' % \
                    (node.host, out)
                return Response(data=msg, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if node_manager.is_valid() is not True:
                self._change_status_failure()
                msg = {}
                msg['message'] = 'A Node status is NOT OK'
                return Response(data=msg, 
                    status=status.HTTP_428_PRECONDITION_REQUIRED)

            # change node status
            changed_status = {'status':'running'}

        elif next_node_stat == 'sync':
            ''' 
            check current node status and report a status
            if a node is normal(runnig) = running (dont change)
            if a node is not running = disturbed (change a status)
            changed_status = {'status' : 'disturbed' }
            '''
            pass

        elif next_node_stat == 'drain':
            '''
            if a node drain action:
                changed_status = {'status': 'unscheduled'}
            '''
            changed_status = {'status': 'unscheduled'}

        elif next_node_stat == 'uninstall':
            '''
            if a node uninstall action:
                changed_status = {'status': 'eliminated'}
            '''
            
            node_manager = NodeManager(serializer.data)

            if str(node.status) == 'plain' or str(node.status) == 'eliminated':
                msg['message'] = \
                    'a Node status is not suitable to uninstall '
                return Response(data=msg, 
                    status=status.HTTP_406_NOT_ACCEPTABLE)

            if str(node.status) == 'running':
                # if node status runnig -> drain a node first
                msg['message'] = \
                    'a Node status is running, Drain first  '
                return Response(data=msg, 
                    status=status.HTTP_428_PRECONDITION_REQUIRED)
                    

            if 'master' in node.roles:
                node_qs = Node.objects.filter(
                    cluster=node.cluster).filter(
                        status='running').exclude(uuid=node.uuid)

                if len(node_qs) > 0:
                    msg['message'] = \
                        'Cluster(%s) has a running node(%d)' %(
                        node.cluster.uuid, len(node_qs))

                    return Response(data=msg,
                        status=status.HTTP_428_PRECONDITION_REQUIRED)

            res = node_manager.stopNode()

            if not res:
                msg['message'] = \
                    'To stop %s node is Fail' % (node.host)
                return Response(data=msg, 
                    status=status.HTTP_406_NOT_ACCEPTABLE)
                
            res, out = node_manager.unInstallNode(cluster)

            if not res:
                msg['message'] = \
                    'Uninstall node %s is Fail(%s)' % (node.host, out)
                return Response(data=msg, 
                    status=status.HTTP_406_NOT_ACCEPTABLE)
            
            res, out = node_manager.removeNode(cluster)

            if not res:
                msg['message'] = \
                    'remove node meta %s is Fail(%s)' % (node.host, out)
                return Response(data=msg, 
                    status=status.HTTP_406_NOT_ACCEPTABLE)
                
            changed_status = {'status': 'eliminated'}

        elif next_node_stat == 'plain':
            # only test
            changed_status = {'status': 'plain'}

        serializer.update(node, changed_status)

        return Response(serializer.data, status.HTTP_201_CREATED)


@permission_classes((permissions.AllowAny,))
class NodeViewer(APIView):
    """ 
    Node resource viewer:
    return the Node
    """

    def get_object(self, uuid):

        try:
            return Node.objects.get(uuid=uuid)
        except Node.DoesNotExist:
            raise Http404

    def has_duplicate(self, **query):

        msg = {}
        try:
            node_qs = Node.objects.all().filter(**query)

            if node_qs.exists():
                msg['message'] = ' object is duplicated'
                return True, msg

            else:
                return False, msg

        except Node.DoesNotExist:
            raise Http404

    def get(self, request, uuid=None, format=None):
        """ 
        Node resource 정보 조회  
        ---
        serializer: 
            - NodeSerializer

        parameters:
            - name: uuid
              description: node uuid
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """

        if uuid is None:
            node = Node.objects.all()
            serializer = NodeSerializer(node, many=True)
        else:
            node = self.get_object(uuid)
            serializer = NodeSerializer(node)

        return Response(serializer.data)

    def post(self, request, format=None):
        """ Node resource 생성(NodeViwer)
        ---
        serializer: 
            - NodeSerializer

        parameters:
            - name: uuid
              description: node uuid
              type: string

            - name: name
              description: node name
              type: string

            - name: host
              description: node hostname
              type: string

            - name: ipaddr 
              description: node ip address
              type: ip

            - name: system_info
              description: system infomation accound, keys
              type: dictionary

            - name: roles
              description: node role
              type: array

            - name: component_info 
              description: components which node has
              type: dictionary

            - name: cluster
              description: cluster which node in
              type: string

            - name: tags
              description: node tags
              type: string

            - name: status
              description: node status
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """

        serializer = NodeSerializer(data=request.data)
        
        if serializer.is_valid_add_uuid():
            node = serializer.validated_data
            search = {
                'host':node['host'],
                'cluster':node['cluster']
            }
            
            res, msg = self.has_duplicate(**search)

            if res is True:
                return JsonResponse(msg, 
                    status=status.HTTP_428_PRECONDITION_REQUIRED)

            serializer.save()

            return Response(serializer.data,
                status=status.HTTP_201_CREATED)

        return Response(serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, uuid, format=None):
        """ Node resource 정보 변경 
        ---
        serializer: 
            - NodeSerializer

        parameters:
            - name: uuid
              description: node uuid
              type: string

            - name: name
              description: node name
              type: string

            - name: host
              description: node hostname
              type: string

            - name: ipaddr 
              description: node ip address
              type: ip

            - name: system_info
              description: system infomation accound, keys
              type: dictionary

            - name: roles
              description: node role
              type: array

            - name: component_info 
              description: components which node has
              type: dictionary

            - name: cluster
              description: cluster which node in
              type: string

            - name: tags
              description: node tags
              type: string

            - name: status
              description: node status
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """ 
        # update a node
        node = self.get_object(uuid)
       
        if request.data['status'] != str(node.status):
            msg = {}
            msg['message'] = 'You cannot change node status'
            return Response(data=msg, 
                status=status.HTTP_400_BAD_REQUEST)

        serializer = NodeSerializer(node, data=request.data)

        if serializer.is_valid_add_uuid():
            serializer.update(node, serializer.validated_data) 

            return Response(serializer.data)

        return Response(serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, uuid, format=None):
        """ Node resource 정보 삭제 
        ---
        serializer: 
            - NodeSerializer

        parameters:
            - name: uuid
              description: node uuid
              type: string

        responseMessages:
            - code: 204
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """

        # delete a node
        node = self.get_object(uuid)
        serializer = NodeSerializer(node)

        # check a node status(enable/disable) 
        msg = {}
        if str(serializer.data['status']) == 'eliminated' or \
            str(serializer.data['status']) == 'plain':
            
            serializer.delete(node)

            msg['message'] = ' Successful Deletion'
            return Response(data=msg, 
                status=status.HTTP_200_OK)
        else:
        
            msg['message'] = ' Delete failed (reason: node status is not proper)'
            return Response(data=msg, 
                status=status.HTTP_428_PRECONDITION_REQUIRED)


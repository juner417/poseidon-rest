# -*- coding: utf-8 -*-
import time
import os
import re
import sys
import json
import ast
import logging
from nodes.models import Node
from clusters.models import Cluster
from components.models import Component
from nodes.serializers import NodeSerializer
from clusters.serializers import ClusterSerializer
from components.serializers import ComponentSerializer
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from rest_framework import status, permissions

@permission_classes((permissions.AllowAny,))
class ComponentJoinViewer(APIView):
    """ Component resource Join viewer with Cluster and Node """

    def __init__(self):
        APIView.__init__(self)
        self.logger = logging.getLogger(__name__)

    def get(self, request, uuid, component_uuid=None, format=None):
        """ 입력한 uuid에 속한 component 조회 """ 

        if re.search('cluster-', uuid):
            flag = 'cluster'
            parent_obj = Cluster.objects.get(uuid=uuid)
        elif re.search('node-', uuid):
            flag = 'node'
            parent_obj = Node.objects.get(uuid=uuid)
            node_roles = [str(x) for x in parent_obj.roles]
        
        if component_uuid is None:
            if flag == 'cluster':
                component = Component.objects.filter(
                    cluster=parent_obj.uuid)
            elif flag == 'node':
                component = Component.objects.filter(
                    role__in=node_roles)
        else:
            if flag == 'cluster':
                components = Component.objects.filter(
                    cluster=parent_obj.uuid,
                    uuid=component_uuid)
            elif flag == 'node':
                component = Component.objects.filter(
                    role__in=node_roles,
                    uuid=component_uuid)

        if len(component) == 0:
            msg = {} 
            msg['message'] = '%s has not components' % uuid
            return Response(data=msg,
                status=status.HTTP_404_NOT_FOUND)

        serializer = ComponentSerializer(component, many=True)

        return Response(serializer.data)
                
@permission_classes((permissions.AllowAny,))
class ComponentController(APIView):
    """ Component resource controller """

    def __init__(self):

        APIView.__init__(self)
        self.logger = logging.getLogger(__name__)

    def get_object(self, uuid):

        try:
            return Component.objects.get(uuid=uuid)

        except Node.DoesNotExist:
            raise Http404

    def has_duplicate(self, **query):

        msg = {}
        try:
            comp_qs = Component.objects.all().filter(**query)

            if comp_qs.exists():
                msg['message'] = ' object is duplicated'
                return True, msg

            else:
                return False, msg

        except Node.DoesNotExist:
            raise Http404

    def get(self, request, uuid=None, format=None):
        """ Component resource 조회 
        ---
        serializer:
            - ComponentSerializer

        parameters:
            - name: uuid
              description: component uuid
              required: false
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
            component = Component.objects.all()
            serializer = ComponentSerializer(component, many=True)
        else:
            component = self.get_object(uuid)
            serializer = ComponentSerializer(component)

        return Response(serializer.data)

    def post(self, request, format=None):
        """ Component resource 생성
        ---
        serializer:
            - ComponentSerializer

        parameters:
            - name: name
              description: component uuid
              required: false
              type: string

            - name: role
              description: components role
              type: string

            - name: opts
              description: components options
              type: dictionary

            - name: cluster
              description: cluster uuid
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """

        serializer = ComponentSerializer(data=request.data)

        if serializer.is_valid_add_uuid():
            compo = serializer.validated_data
            
            search = { 'name': compo['name'], 'role': compo['role'], 'cluster': compo['cluster'] }

            res, msg = self.has_duplicate(**search)
            
            if res is True:
                return JsonResponse(msg, status=status.HTTP_428_PRECONDITION_REQUIRED)

            serializer.save()

            return Response(serializer.data,
                status=status.HTTP_201_CREATED)

        return Response(serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, uuid, format=None):
        """ Component resource 변경
        ---
        serializer:
            - ComponentSerializer

        parameters:
            - name: name
              description: component uuid
              required: false
              type: string

            - name: role
              description: components role
              type: string

            - name: opts
              description: components options
              type: dictionary

            - name: cluster
              description: cluster uuid
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """

        component = self.get_object(uuid)
        serializer = ComponentSerializer(component,data=request.data)

        if serializer.is_valid_add_uuid():
            # serializer.update(self, instance, validated_data)
            serializer.update(component, serializer.validated_data)
            return Response(serializer.data)

        return Response(serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, uuid, format=None):
        """ Component resource 삭제 
        ---
        serializer:
            - ComponentSerializer

        parameters:
            - name: uuid
              description: component uuid
              required: false
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """

        component = self.get_object(uuid)

        serializer = ComponentSerializer(component)
        serializer.delete(component)

        msg = {}
        msg['message'] = ' Successful Deletion'

        return Response(data=msg, status=status.HTTP_200_OK)

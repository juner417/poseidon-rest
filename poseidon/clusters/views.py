# -*- coding: utf-8 -*-
import time
import os
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


# Create your views here.
@permission_classes((permissions.AllowAny,))
class ClusterController(APIView):
    """ Cluster resource status controller """
    def get_object(self, uuid):
        try:
            return Cluster.objects.get(uuid=uuid)
        except Node.DoesNotExist:
            raise Http404

    def has_duplicate(self, **query):
        msg = {}
        try:
            cluster_qs = Cluster.objects.all().filter(**query)

            if cluster_qs.exists():
                msg['message'] = ' object is duplicated'
                return True, msg

            else:
                return False, msg

        except Node.DoesNotExist:
            raise Http404
    
    def get(self, request, uuid=None, format=None):
        """ Cluster resource 조회
        ---
        serializer:
            - ClusterSerializer

        parameters:
            - name: uuid
              description: cluster uuid
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
            cluster = Cluster.objects.all()
            serializer = ClusterSerializer(cluster, many=True)
        else:
            cluster = self.get_object(uuid)
            serializer = ClusterSerializer(cluster)

        return Response(serializer.data)

    def post(self, request, format=None):
        """ Cluster resource 생성
        ---
        serializer:
            - ClusterSerializer

        parameters:
            - name: name
              description: cluster name
              type: string

            - name: master
              description: cluster master server
              type: string

            - name: port
              description: cluster master port
              type: string

            - name: proxy
              description: cluster deploy/proxy server ip
              type: string

            - name: cluster_engine
              description: cluster orchestration engine
              type: string

            - name: platform_info
              description: cluster platform information
              type: dictionary

            - name: network_info
              description: cluster vitual network information
              type: dictionary

            - name: metas
              description: cluster meta
              type: array

            - name: capacity_info
              description: cluster capacity information
              type: dictionary

            - name: tags
              description: tags
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """

        serializer = ClusterSerializer(data=request.data)

        if serializer.is_valid_add_uuid():
            clo = serializer.validated_data
            
            search = { 'name': clo['name'], 'master': clo['master'] }

            res, msg = self.has_duplicate(**search)

            if res is True:
                return JsonResponse(msg, status=status.HTTP_428_PRECONDITION_REQUIRED)

            serializer.save()

            return Response(serializer.data,
                status=status.HTTP_201_CREATED)

        return Response(serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, uuid, format=None):
        """ Cluster resource 변경
        ---
        serializer:
            - ClusterSerializer

        parameters:
            - name: name
              description: cluster name
              type: string

            - name: master
              description: cluster master server
              type: string

            - name: port
              description: cluster master port
              type: string

            - name: proxy
              description: cluster deploy/proxy server ip
              type: string

            - name: cluster_engine
              description: cluster orchestration engine
              type: string

            - name: platform_info
              description: cluster platform information
              type: dictionary

            - name: network_info
              description: cluster vitual network information
              type: dictionary

            - name: metas
              description: cluster meta
              type: array

            - name: capacity_info
              description: cluster capacity information
              type: dictionary

            - name: tags
              description: tags
              type: string

        responseMessages:
            - code: 200
              message: OK

        consumes:
            - application/json

        produces:
            - application/json
        """

        cluster = self.get_object(uuid)
        serializer = ClusterSerializer(cluster,data=request.data)

        if serializer.is_valid_add_uuid():
            serializer.update(cluster, serializer.validated_data)
            return Response(serializer.data)

        return Response(serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, uuid, format=None):
        """ Cluster resource 삭제
        ---
        serializer:
            - ClusterSerializer

        parameters:
            - name: uuid
              description: node uuid
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

        cluster = self.get_object(uuid)
        serializer = ClusterSerializer(cluster)

        search = { 'cluster': str(cluster.uuid) }
        node = Node.objects.all().filter(**search)
        component = Node.objects.all().filter(**search)

        msg = {}
        if node.count() == 0 and component.count() == 0:

            serializer.delete(cluster)
            msg['message'] = ' Successful Deletion'

        else:
            msg['message'] = 'cluster has a related node or component'
            return Response(data=msg, status=status.HTTP_428_PRECONDITION_REQUIRED)
            
        return Response(data=msg, status=status.HTTP_200_OK)


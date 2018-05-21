from __future__ import unicode_literals
from django.db import models
from django.forms.models import model_to_dict
from jsonfield import JSONField
from clusters.models import Cluster
import uuid

# Create your models here.
'''
    [fieldname]_info = dictionary
    [fieldname]s = array
'''

class Node(models.Model):
    # system_info = {os:,account:,pubkey:,pemkey:}
    # role = [ kubelet,kube-proxy,flanneld,docker,...]
    # component_info = {component:version,...}
    # status = plain|running|disturbed|unscheduled|eliminated
    # custom_id = '%s-%s' %('node', str(uuid.uuid4())[:8])
    uuid = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    host = models.CharField(max_length=200)
    ipaddr = models.GenericIPAddressField()
    system_info = JSONField()
    roles = JSONField()
    component_info = JSONField()
    cluster = models.ForeignKey(Cluster, to_field='uuid')
    #cpu = models.FloatField()
    #mem = models.FloatField()
    #disk = models.FloatField()
    tags = JSONField()
    status = models.CharField(max_length=50, default='plain')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "/poseidon/v1/api/nodes/%s" % self.uuid

    def __unicode__(self):
        return self.host

    class Meta:
        ordering = ('host',)

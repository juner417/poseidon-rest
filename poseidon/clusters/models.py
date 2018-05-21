from __future__ import unicode_literals
from django.db import models
from django.forms.models import model_to_dict
from jsonfield import JSONField
import uuid

# Create your models here.
'''
    [fieldname]_info = dictionary
    [fieldname]s = array
'''

class Cluster(models.Model):
    # Need a custom uuid.  

    # platform_info = {os:, account:, pubkey:, pemkey: }
    # network_info(overlay's info-flannel) = {Network:, backend:, type:)
    # metas = [ etcd clusters ]
    # capacity_info = {node:,cpu:,memory:}
    uuid = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    master = models.GenericIPAddressField()
    port = models.CharField(max_length=10)
    proxy = models.CharField(max_length=30)
    cluster_engine = models.CharField(max_length=20, default='kubernetes')
    platform_info = JSONField()
    network_info = JSONField()
    metas = JSONField()
    capacity_info = JSONField()
    tags = JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s: %s' % (self.uuid, self.name)

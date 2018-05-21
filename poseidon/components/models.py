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

class Component(models.Model):

    # opts = {optname:values,...}
    uuid = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=30)
    role = models.CharField(max_length=30)
    opts = JSONField()
    cluster = models.ForeignKey(Cluster, to_field='uuid')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

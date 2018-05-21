from rest_framework import serializers
from clusters.models import Cluster
from django.forms.models import model_to_dict
import uuid

# serializer : serialize/deserialize a data formed json

class ClusterSerializer(serializers.ModelSerializer):

    platform_info = serializers.JSONField()
    network_info = serializers.JSONField()
    metas = serializers.JSONField()
    capacity_info = serializers.JSONField()
    tags = serializers.JSONField()

    def is_valid_add_uuid(self):
    # add a custom id for uuid field

        if self.initial_data:
            
            if self.instance is not None:
                # update
                self.initial_data['uuid'] = self.instance.uuid
            else:
                # create
                prefix = self.Meta.model.__name__.lower()
                self.initial_data['uuid'] = '%s-%s' %(prefix, str(uuid.uuid4())[:8])

            self.is_valid()

            return not bool(self._errors)

    def delete(self, instance):
        instance.delete()

    class Meta:
        model = Cluster
        ordering = ('uuid','name','master','port',)
        exclude = ('id',)

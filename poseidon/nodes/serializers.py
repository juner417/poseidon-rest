from rest_framework import serializers
from nodes.models import Node
from django.forms.models import model_to_dict
import uuid

# serializer : serialize/deserialize a data formed json

class NodeSerializer(serializers.ModelSerializer):

    system_info = serializers.JSONField()
    roles = serializers.JSONField()
    component_info = serializers.JSONField()
    tags = serializers.JSONField()
    url = serializers.URLField(source='get_absolute_url', read_only=True)

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
        model = Node
        ordering = ('uuid','name','role','cluster',)
        exclude = ('id',)

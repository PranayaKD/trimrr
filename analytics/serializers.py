from rest_framework import serializers
from .models import ClickEvent

class ClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClickEvent
        fields = ['timestamp', 'ip_address', 'device', 'browser', 'country', 'city', 'referrer']

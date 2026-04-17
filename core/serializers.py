from rest_framework import serializers
from .models import ShortenedLink

class LinkSerializer(serializers.ModelSerializer):
    total_clicks = serializers.SerializerMethodField()
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = ShortenedLink
        fields = [
            'id', 'original_url', 'short_code', 'custom_alias', 
            'title', 'is_active', 'created_at', 'expires_at', 
            'short_url', 'total_clicks'
        ]
        read_only_fields = ['short_code', 'created_at']

    def get_total_clicks(self, obj):
        return obj.clicks.count()

    def get_short_url(self, obj):
        request = self.context.get('request')
        code = obj.custom_alias or obj.short_code
        if request:
            return request.build_absolute_uri(f'/{code}/')
        return f'/{code}/'

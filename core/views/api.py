"""
core/views/api.py
REST API views — completely separate from the template rendering layer.
"""
from django.db import IntegrityError, models
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.models import ClickEvent
from analytics.serializers import ClickSerializer
from core.models import ShortenedLink
from core.serializers import LinkSerializer
from core.views.helpers import (
    safe_cache_delete,
    validate_url_safety,
    validate_alias,
)


class LinkListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        links = (
            ShortenedLink.objects
            .filter(owner=request.user)
            .order_by('-created_at')
        )
        serializer = LinkSerializer(links, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = LinkSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        original_url = request.data.get('original_url', '')
        custom_alias = request.data.get('custom_alias', '').strip() or None

        # ── Validation ──────────────────────────────────────────
        is_safe, safety_error = validate_url_safety(original_url)
        if not is_safe:
            return Response({'error': safety_error}, status=status.HTTP_400_BAD_REQUEST)

        is_valid_alias, alias_error = validate_alias(custom_alias)
        if not is_valid_alias:
            return Response({'error': alias_error}, status=status.HTTP_400_BAD_REQUEST)

        if custom_alias:
            alias_taken = ShortenedLink.objects.filter(
                models.Q(short_code=custom_alias) | models.Q(custom_alias=custom_alias)
            ).exists()
            if alias_taken:
                return Response(
                    {'error': 'Alias already taken.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        short_code = ShortenedLink.generate_code()

        try:
            serializer.save(owner=request.user, short_code=short_code)
        except IntegrityError:
            return Response(
                {'error': 'A collision occurred. Please try again.'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LinkDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _get_link(identifier, user):
        return get_object_or_404(
            ShortenedLink,
            models.Q(short_code=identifier) | models.Q(custom_alias=identifier),
            owner=user,
        )

    def get(self, request, short_code):
        link = self._get_link(short_code, request.user)
        serializer = LinkSerializer(link, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, short_code):
        link = self._get_link(short_code, request.user)
        link.is_active = not link.is_active
        link.save(update_fields=['is_active'])

        # Invalidate cache
        safe_cache_delete(f"link:{short_code}")
        if link.custom_alias:
            safe_cache_delete(f"link:{link.custom_alias}")

        return Response({'is_active': link.is_active})

    def delete(self, request, short_code):
        link = self._get_link(short_code, request.user)
        safe_cache_delete(f"link:{short_code}")
        if link.custom_alias:
            safe_cache_delete(f"link:{link.custom_alias}")
        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LinkStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, short_code):
        link = get_object_or_404(
            ShortenedLink,
            models.Q(short_code=short_code) | models.Q(custom_alias=short_code),
            owner=request.user,
        )

        clicks_per_day = (
            ClickEvent.objects.filter(link=link)
            .annotate(date=TruncDate('timestamp'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        recent_clicks = link.clicks.all().order_by('-timestamp')[:10]

        return Response({
            'total_clicks': link.clicks.count(),
            'clicks_per_day': list(clicks_per_day),
            'recent_clicks': ClickSerializer(recent_clicks, many=True).data,
        })

"""Read-only public API under /api/, for the Next.js frontend. Same visibility rules as the site's own pages."""

from django.conf import settings
from django.db.models import Prefetch, Q
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Chef, ChefPackage, City, Review, ServiceCategory
from .serializers import (
    ChefCardSerializer, ChefDetailSerializer, CitySerializer, PackageWithChefSerializer, ReviewSerializer,
    ServiceSerializer,
)
from .views import filter_marketplace


class MarketplacePagination(PageNumberPagination):
    page_size = 12  # same as the marketplace page


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceSerializer
    pagination_class = None
    lookup_field = 'slug'


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    pagination_class = None
    lookup_field = 'slug'


class ChefViewSet(viewsets.ReadOnlyModelViewSet):
    """Live chefs. The list takes the marketplace filters: ?service=, ?city=, ?q=, ?sort=, ?page=, plus ?featured=1."""

    lookup_field = 'slug'
    pagination_class = MarketplacePagination

    def get_queryset(self):
        if self.action == 'list':
            chefs = filter_marketplace(self.request.query_params)[0]
            if self.request.query_params.get('featured'):
                chefs = chefs.filter(is_featured=True)
            return chefs

        visible = Q(is_active=True)
        if self.request.user.is_authenticated:
            visible |= Q(user=self.request.user)  # chefs can preview their own profile before it goes live
        return Chef.objects.filter(visible).with_ratings().select_related('city').prefetch_related(
            'services', 'photos',
            Prefetch('packages', queryset=ChefPackage.objects.filter(is_active=True).select_related('service')),
        )

    def get_serializer_class(self):
        return ChefCardSerializer if self.action == 'list' else ChefDetailSerializer

    @action(detail=True)
    def reviews(self, request, slug=None):
        chef = self.get_object()
        page = self.paginate_queryset(chef.reviews.filter(status=Review.Status.PUBLISHED).select_related('chef'))
        return self.get_paginated_response(ReviewSerializer(page, many=True).data)


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Packages on offer from live chefs, featured chefs first. Takes ?service=."""

    serializer_class = PackageWithChefSerializer
    pagination_class = MarketplacePagination

    def get_queryset(self):
        packages = (
            ChefPackage.objects.filter(chef__is_active=True, is_active=True)
            .select_related('chef__city', 'service')
            .order_by('-chef__is_featured', 'order', 'price')
        )
        if service := self.request.query_params.get('service'):
            packages = packages.filter(service__slug=service)
        return packages


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """Published reviews of live chefs, newest first. Takes ?min_rating= (the homepage uses 4)."""

    serializer_class = ReviewSerializer
    pagination_class = MarketplacePagination

    def get_queryset(self):
        reviews = Review.objects.filter(status=Review.Status.PUBLISHED, chef__is_active=True).select_related('chef')
        min_rating = self.request.query_params.get('min_rating', '')
        if min_rating.isdigit():
            reviews = reviews.filter(rating__gte=int(min_rating))
        return reviews


@api_view(['GET'])
def stats(request):
    """The counts shown on the homepage."""
    live_chefs = Chef.objects.live()
    return Response({
        'chefs': live_chefs.count(),
        'verified': live_chefs.filter(is_verified=True).count(),
        'packages': ChefPackage.objects.filter(chef__is_active=True, is_active=True).count(),
        'cities': City.objects.filter(chefs__is_active=True).distinct().count(),
    })


@api_view(['GET'])
def site(request):
    """Contact and payment details shown around the site, so they stay set in one place."""
    return Response({
        'whatsapp_url': settings.WHATSAPP_URL,
        'whatsapp_display': settings.WHATSAPP_DISPLAY,
        'mpesa_paybill': settings.MPESA_PAYBILL,
        'social_links': [{'icon': icon, 'url': url} for icon, url in settings.SOCIAL_LINKS.items() if url],
    })

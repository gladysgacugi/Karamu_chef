"""The team pages (the phone-friendly admin) as a JSON API under /api/team/, for the Next.js frontend. Staff only.

Works like api_chef.py, with the same functions as the Django team pages in views.py. Lists take the same ?status=
(missing means the default tab, empty means all), ?show= and ?payment= as the pages.
"""

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .api_chef import answer
from .api_forms import FormEndpoint, form_fields
from .forms import ApproveApplicationForm, RejectApplicationForm, TeamBookingForm
from .models import BookingRequest, Chef, ChefApplication, ChefMatchRequest, ContactMessage, Review
from .serializers import (
    ApplicationDetailSerializer, ApplicationSerializer, BookingMessageSerializer, ContactMessageSerializer,
    MatchRequestSerializer, TeamBookingSerializer, TeamChefSerializer, TeamReviewSerializer,
)
from .views import (
    CHEF_SWITCHES, TEAM_BOOKING_SAVED, booking_clash, change_booking_status, mark_replied, set_payment_status,
    set_request_status, set_review_status, switch_chef, team_application_list, team_approve, team_booking_list,
    team_chef_list, team_inbox_list, team_reject, team_request_list, team_review_list, team_upcoming, team_waiting,
)


def team_api(view):
    return permission_classes([IsAdminUser])(view)


def tabbed(items, serializer, tabs):
    return Response({'items': serializer(items, many=True).data, **tabs})


@api_view(['GET'])
@team_api
def waiting(request):
    """The counts for the badges on the bottom menu."""
    return Response(team_waiting())


@api_view(['GET'])
@team_api
def home(request):
    return Response({
        'first_name': request.user.first_name or request.user.username,
        'waiting': team_waiting(),
        'upcoming': TeamBookingSerializer(team_upcoming(), many=True).data,
        'chefs_waiting_to_go_live': Chef.objects.filter(is_active=False).count(),
    })


# ---------------------------------------------------------------------------
# Chefs and applications
# ---------------------------------------------------------------------------

@api_view(['GET'])
@team_api
def applications(request):
    items, status, tabs = team_application_list(request.query_params)
    return tabbed(items, ApplicationSerializer, tabs)


@api_view(['GET'])
@team_api
def application(request, pk):
    """An application, with the approve and reject forms while it has no chef profile."""
    app = get_object_or_404(ChefApplication.objects.prefetch_related('dish_photos'), pk=pk)
    return Response({
        'application': ApplicationDetailSerializer(app).data,
        'approve_fields': form_fields(ApproveApplicationForm()),
        'reject_fields': form_fields(RejectApplicationForm()),
    })


@api_view(['POST'])
@team_api
def approve_application(request, pk):
    return answer(*team_approve(get_object_or_404(ChefApplication, pk=pk), request.POST))


@api_view(['POST'])
@team_api
def reject_application(request, pk):
    return answer(*team_reject(get_object_or_404(ChefApplication, pk=pk), request.POST))


@api_view(['GET'])
@team_api
def chefs(request):
    items, show, filters = team_chef_list(request.query_params.get('show'))
    return Response({'items': TeamChefSerializer(items, many=True).data, 'show': show, 'filters': filters})


@api_view(['POST'])
@team_api
def chef_switch(request, pk, switch):
    """Put a chef live, on the homepage or verified ("on": "1"), or take them off ("0")."""
    if switch not in CHEF_SWITCHES:
        raise Http404
    return Response({'message': switch_chef(get_object_or_404(Chef, pk=pk), switch, request.POST.get('on') == '1')})


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

@api_view(['GET'])
@team_api
def bookings(request):
    items, checking_payments, tabs = team_booking_list(request.query_params)
    return Response({'items': TeamBookingSerializer(items, many=True).data, 'checking_payments': checking_payments, **tabs})


class BookingEndpoint(FormEndpoint):
    """A booking with its messages and review, and the form to change the price and team notes."""

    permission_classes = [IsAdminUser]

    def load(self):
        self.booking = get_object_or_404(BookingRequest.objects.select_related('chef', 'package', 'customer'), pk=self.kwargs['pk'])

    def get_form(self, data=None, files=None):
        return TeamBookingForm(data, instance=self.booking)

    def describe(self, form):
        review = getattr(self.booking, 'review', None)
        return {
            **super().describe(form),
            'booking': TeamBookingSerializer(self.booking).data,
            'messages': BookingMessageSerializer(self.booking.messages.all(), many=True).data,
            'review': TeamReviewSerializer(review).data if review else None,
            'clash': booking_clash(self.booking),
        }

    def save(self, form):
        form.save()
        return {'message': TEAM_BOOKING_SAVED, 'redirect': reverse('team_booking', args=[self.booking.pk])}


@api_view(['POST'])
@team_api
def booking_status(request, pk):
    booking = get_object_or_404(BookingRequest.objects.select_related('chef'), pk=pk)
    return answer(*change_booking_status(booking, request.POST, by_team=True))


@api_view(['POST'])
@team_api
def booking_payment(request, pk):
    booking = get_object_or_404(BookingRequest.objects.select_related('chef'), pk=pk)
    return answer(*set_payment_status(booking, request.POST.get('payment_status')))


# ---------------------------------------------------------------------------
# Reviews, find-a-chef requests and the contact inbox
# ---------------------------------------------------------------------------

@api_view(['GET'])
@team_api
def reviews(request):
    items, status, tabs = team_review_list(request.query_params)
    return tabbed(items, TeamReviewSerializer, tabs)


@api_view(['POST'])
@team_api
def review_status(request, pk):
    message = set_review_status(get_object_or_404(Review.objects.select_related('chef'), pk=pk), request.POST.get('status'))
    return Response({'message': message} if message else {})


@api_view(['GET'])
@team_api
def requests(request):
    items, status, tabs = team_request_list(request.query_params)
    return tabbed(items, MatchRequestSerializer, tabs)


@api_view(['POST'])
@team_api
def request_status(request, pk):
    message = set_request_status(get_object_or_404(ChefMatchRequest, pk=pk), request.POST.get('status'))
    return Response({'message': message} if message else {})


@api_view(['GET'])
@team_api
def inbox(request):
    items, show_all = team_inbox_list(request.query_params.get('show'))
    return Response({'items': ContactMessageSerializer(items, many=True).data, 'show_all': show_all})


@api_view(['POST'])
@team_api
def message_replied(request, pk):
    return Response({'message': mark_replied(get_object_or_404(ContactMessage, pk=pk))})

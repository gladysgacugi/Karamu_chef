"""The chef dashboard as a JSON API under /api/chef/, for the Next.js frontend. Only for logged-in chefs.

Works like api_forms.py: GET describes the page and its form, POST answers 400 {"errors": {...}} or
200 {"message", "warning", "redirect"} (any can be missing). Each endpoint does what the Django page does, with the same
functions from views.py.
"""

from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from .api_forms import FormEndpoint, error, formset_json, invalid
from .forms import MAX_CHEF_PHOTOS, ChefDocumentsForm
from .models import BookingRequest, Chef, ChefTimeOff
from .serializers import (
    BookingMessageSerializer, ChefBookingSerializer, OwnChefSerializer, TimeOffSerializer,
)
from .views import (
    TIME_OFF_REMOVED, change_booking_status, chef_bookings, chef_message_form, chef_message_sent, chef_photo_forms,
    chef_profile_forms, save_chef_documents, save_chef_photos, save_chef_profile, save_time_off, send_booking_message,
    set_accepting_bookings, time_off_form, upcoming_confirmed,
)


class IsChef(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and Chef.objects.filter(user=request.user).exists()


def answer(worked, message):
    return Response({'message': message}) if worked else error(message)


class ChefEndpoint(FormEndpoint):
    """A chef dashboard page. GET describes it, POST saves its form."""

    permission_classes = [IsChef]

    def load(self):
        self.chef = self.request.user.chef_profile

    def describe(self, form):
        return {**super().describe(form), 'chef': OwnChefSerializer(self.chef).data}


class DashboardEndpoint(ChefEndpoint):
    """The chef's bookings. Takes ?status=."""

    def get(self, request, *args, **kwargs):
        bookings, tabs = chef_bookings(self.chef, request.query_params.get('status'))
        return Response({
            'chef': OwnChefSerializer(self.chef).data,
            'bookings': ChefBookingSerializer(bookings, many=True).data,
            **tabs,
        })


class BookingEndpoint(ChefEndpoint):
    """One booking with the messages, and the box to write to the customer."""

    def load(self):
        super().load()
        self.booking = get_object_or_404(self.chef.bookings.select_related('package'), pk=self.kwargs['pk'])

    def get_form(self, data=None, files=None):
        return chef_message_form(self.booking, data)

    def describe(self, form):
        return {
            **super().describe(form),
            'booking': ChefBookingSerializer(self.booking).data,
            'messages': BookingMessageSerializer(self.booking.messages.all(), many=True).data,
        }

    def save(self, form):
        send_booking_message(self.booking, form, from_chef=True)
        return {'message': chef_message_sent(self.booking),
                'redirect': f"{reverse('chef_booking', args=[self.booking.pk])}#messages"}


@api_view(['POST'])
@permission_classes([IsChef])
def booking_status(request, pk):
    """Confirm (with the price), complete, decline or cancel."""
    booking = get_object_or_404(BookingRequest, pk=pk, chef=request.user.chef_profile)
    return answer(*change_booking_status(booking, request.POST))


class AvailabilityEndpoint(ChefEndpoint):
    """Days away and confirmed bookings coming up, and the form to add time off."""

    def get_form(self, data=None, files=None):
        return time_off_form(self.chef, data)

    def describe(self, form):
        return {
            **super().describe(form),
            'time_off': TimeOffSerializer(self.chef.upcoming_time_off(), many=True).data,
            'upcoming': ChefBookingSerializer(upcoming_confirmed(self.chef), many=True).data,
        }

    def save(self, form):
        message, warning = save_time_off(self.chef, form)
        return {'message': message, 'warning': warning, 'redirect': reverse('chef_availability')}


@api_view(['POST'])
@permission_classes([IsChef])
def accepting(request):
    """Pause new bookings ("accepting": "0") or take them again ("1")."""
    return Response({'message': set_accepting_bookings(request.user.chef_profile, request.POST.get('accepting') == '1')})


@api_view(['POST'])
@permission_classes([IsChef])
def delete_time_off(request, pk):
    get_object_or_404(ChefTimeOff, pk=pk, chef=request.user.chef_profile).delete()
    return Response({'message': TIME_OFF_REMOVED})


class ProfileEndpoint(ChefEndpoint):
    """The profile form and the packages formset ("packages-0-name"...), sent together as one form."""

    def get(self, request, *args, **kwargs):
        form, packages = chef_profile_forms(self.chef)
        return Response({**self.describe(form), 'packages': formset_json(packages)})

    def post(self, request, *args, **kwargs):
        form, packages = chef_profile_forms(self.chef, request.POST, request.FILES)
        if not all([form.is_valid(), packages.is_valid()]):
            return invalid(form, packages)
        return Response({'message': save_chef_profile(self.chef, form, packages), 'redirect': reverse('chef_profile_edit')})


class PhotosEndpoint(ChefEndpoint):
    """The gallery formset ("photos-0-caption"...) with each photo, and the new_photos upload, as one form."""

    def get(self, request, *args, **kwargs):
        photos, add = chef_photo_forms(self.chef)
        return Response({
            **self.describe(add),
            'photos': formset_json(photos),
            'images': [form.instance.image.url for form in photos],
            'max_photos': MAX_CHEF_PHOTOS,
        })

    def post(self, request, *args, **kwargs):
        photos, add = chef_photo_forms(self.chef, request.POST, request.FILES)
        if not all([photos.is_valid(), add.is_valid()]):
            return invalid(photos, add)
        return Response({'message': save_chef_photos(self.chef, photos, add), 'redirect': reverse('chef_photos')})


class DocumentsEndpoint(ChefEndpoint):
    """The ID and food handler's certificate. Each field's "url" is the file uploaded now."""

    def get_form(self, data=None, files=None):
        return ChefDocumentsForm(data, files, instance=self.chef)

    def save(self, form):
        return {'message': save_chef_documents(form), 'redirect': reverse('chef_documents')}

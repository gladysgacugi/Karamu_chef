"""The customer forms and accounts as a JSON API under /api/, for the Next.js frontend.

Each endpoint reuses the site's Django form and save function, so the checks, messages and emails are the same as on
the Django pages. GET describes the form (fields, labels, choices and starting values, as the templates render them).
POST takes the form as multipart data and answers 400 {"errors": {field or "__all__": [messages]}} or
200 {"message", "redirect"} (either can be missing).

Logins use the site's session cookie, so the frontend must be served from the same address as /api/ (Next.js
forwards it, see frontend/next.config.ts).
"""

from django import forms
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import (
    BookingRequestForm, ChefApplicationForm, ChefMatchRequestForm, ContactForm, EmailLoginForm, PaymentForm,
    ReviewForm, SignUpForm, StyledPasswordResetForm, StyledSetPasswordForm, SubscribeForm,
)
from .models import BookingRequest, Chef
from .serializers import CustomerBookingSerializer
from .views import (
    REVIEW_TOO_EARLY, booking_initial, customer_booking, customer_cancel, customer_message_form, home_for, safe_next,
    save_booking, save_chef_application, save_contact_message, save_match_request, save_review, save_subscription,
    send_booking_message, submit_payment, welcome_message,
)

User = get_user_model()


def form_fields(form):
    """The form's fields as the templates render them with {{ field }}."""
    fields = []
    for bound in form:
        widget = bound.field.widget
        extra = {}
        if isinstance(widget, forms.Textarea):
            kind = 'textarea'
        elif isinstance(widget, forms.Select):
            kind = 'select'
        elif isinstance(widget, forms.CheckboxSelectMultiple):
            kind = 'checkboxes'
        else:
            kind = widget.input_type  # text, email, tel, date, number, password, file, checkbox, hidden

        if kind == 'checkbox':
            value = bool(bound.value())
        elif kind == 'file':
            value = ''
            # The file already saved, and whether it can be removed (Django's "Currently: ... Clear")
            current = bound.initial
            extra = {
                'url': current.url if current else '',
                'clearable': isinstance(widget, forms.ClearableFileInput) and not bound.field.required,
            }
        elif kind == 'password':
            value = ''
        else:
            value = widget.format_value(bound.value())
            if isinstance(value, list) and kind != 'checkboxes':  # select widgets format a list of values
                value = value[0] if value else ''
        fields.append({
            'name': bound.html_name,
            'label': str(bound.label),
            'type': kind,
            'required': bound.field.required,
            'help_text': str(bound.help_text),
            'attrs': {**widget.attrs, **({'multiple': True} if getattr(widget, 'allow_multiple_selected', False) else {})},
            'choices': [[str(v), str(label)] for v, label in widget.choices] if kind in ('select', 'checkboxes') else [],
            'value': value if value is not None else '',
            **extra,
        })
    return fields


def formset_json(formset):
    """A formset: its management fields (TOTAL_FORMS...) and each form's fields."""
    return {
        'management': form_fields(formset.management_form),
        'forms': [form_fields(form) for form in formset],
    }


def form_errors(form):
    """The form's errors by field name as the browser sends it (with the formset prefix), "__all__" for the form."""
    errors = form.errors.get_json_data()
    return {
        name if name == '__all__' else form.add_prefix(name): [e['message'] for e in errs]
        for name, errs in errors.items()
    }


def invalid(*forms_and_formsets):
    """400 with the errors of each form or formset that has any."""
    errors = {}
    for form in forms_and_formsets:
        is_formset = isinstance(form, forms.BaseFormSet)
        for each in (form if is_formset else [form]):
            for name, messages in form_errors(each).items():
                errors.setdefault(name, []).extend(messages)
        if is_formset and form.non_form_errors():
            errors.setdefault('__all__', []).extend(form.non_form_errors())
    return Response({'errors': errors}, status=400)


def error(message, status=400):
    return Response({'errors': {'__all__': [message]}}, status=status)


def user_json(user):
    if not user.is_authenticated:
        return None
    return {
        'first_name': user.first_name,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_chef': Chef.objects.filter(user=user).exists(),
        'home': home_for(user),
    }


class FormEndpoint(APIView):
    """GET describes the form, POST checks it and calls save(form), which returns the JSON answer."""

    form_class = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.load()

    def load(self):
        """Look up what the form is about (a chef, a booking) before GET or POST."""

    def get_form(self, data=None, files=None):
        return self.form_class(data, files)

    def describe(self, form):
        return {'fields': form_fields(form)}

    def get(self, request, *args, **kwargs):
        return Response(self.describe(self.get_form()))

    def post(self, request, *args, **kwargs):
        form = self.get_form(request.POST, request.FILES)
        if not form.is_valid():
            return invalid(form)
        return Response(self.save(form))

    def save(self, form):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------

class ChefApplicationEndpoint(FormEndpoint):
    form_class = ChefApplicationForm

    def save(self, form):
        save_chef_application(form)
        return {'redirect': f"{reverse('become_chef')}?sent=1"}


class MatchRequestEndpoint(FormEndpoint):
    form_class = ChefMatchRequestForm

    def save(self, form):
        return {'message': save_match_request(form)}


class ContactEndpoint(FormEndpoint):
    form_class = ContactForm

    def save(self, form):
        return {'message': save_contact_message(form)}


class SubscribeEndpoint(FormEndpoint):
    form_class = SubscribeForm

    def save(self, form):
        return {'message': save_subscription(form)}


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

class BookingEndpoint(FormEndpoint):
    """A chef's booking form. GET also says what else the chef's profile shows this visitor. Takes ?package=."""

    def load(self):
        user = self.request.user
        visible = Q(is_active=True) | (Q(user=user) if user.is_authenticated else Q())
        self.chef = get_object_or_404(Chef.objects.filter(visible), slug=self.kwargs['slug'])

    def get_form(self, data=None, files=None):
        initial = {'package': self.request.GET.get('package'), **booking_initial(self.request.user)}
        return BookingRequestForm(data, chef=self.chef, initial=initial)

    def describe(self, form):
        user = self.request.user
        to_review = user.bookings.filter(
            chef=self.chef, status=BookingRequest.Status.COMPLETED, review__isnull=True,
        ).first() if user.is_authenticated else None
        return {
            **super().describe(form),
            'logged_in': user.is_authenticated,
            'is_own_profile': user.is_authenticated and self.chef.user_id == user.pk,
            'booking_to_review': {'id': to_review.pk, 'event_date': to_review.event_date} if to_review else None,
        }

    def post(self, request, *args, **kwargs):
        if not self.chef.is_active:  # a chef previewing their hidden profile can't book themselves
            raise Http404
        return super().post(request, *args, **kwargs)

    def save(self, form):
        booking = save_booking(self.request, self.chef, form)
        return {'redirect': reverse('booking_confirmation', args=[booking.pk])}


@api_view(['GET'])
def booking(request, pk):
    """A booking, for its customer only. Takes ?key= from the links in our emails."""
    booking, is_owner = customer_booking(request, pk)
    return Response({**CustomerBookingSerializer(booking, context={'request': request}).data, 'is_owner': is_owner})


class BookingFormEndpoint(FormEndpoint):
    """A form about one of the customer's bookings. Takes ?key= like the booking."""

    def load(self):
        self.booking = customer_booking(self.request, self.kwargs['pk'])[0]
        self.done_url = reverse('booking_confirmation', args=[self.booking.pk])


class PaymentEndpoint(BookingFormEndpoint):
    def get_form(self, data=None, files=None):
        return PaymentForm(data, booking=self.booking)

    def post(self, request, *args, **kwargs):
        if not self.booking.customer_can_pay:
            return Response({'redirect': self.done_url})
        return super().post(request, *args, **kwargs)

    def save(self, form):
        return {'message': submit_payment(self.booking, form.cleaned_data['mpesa_code']), 'redirect': self.done_url}


class ReviewEndpoint(BookingFormEndpoint):
    def get_form(self, data=None, files=None):
        return ReviewForm(data, initial={'customer_name': self.booking.full_name.split()[0]})

    def post(self, request, *args, **kwargs):
        if not self.booking.can_be_reviewed:
            return error(REVIEW_TOO_EARLY if self.booking.status != BookingRequest.Status.COMPLETED
                         else 'You have already reviewed this booking.')
        return super().post(request, *args, **kwargs)

    def save(self, form):
        return {'message': save_review(self.booking, form), 'redirect': self.done_url}


class MessageEndpoint(BookingFormEndpoint):
    """The customer writing to their chef."""

    def get_form(self, data=None, files=None):
        return customer_message_form(self.booking, data)

    def save(self, form):
        send_booking_message(self.booking, form, from_chef=False)
        return {'message': f'Message sent to {self.booking.chef.name}.', 'redirect': f'{self.done_url}#messages'}


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

@api_view(['GET'])
@ensure_csrf_cookie
def me(request):
    """Who is logged in. Also sets the CSRF cookie the frontend sends back with every form."""
    return Response({'user': user_json(request.user)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account(request):
    bookings = request.user.bookings.select_related('chef', 'package', 'review').order_by('-event_date')
    return Response({
        'user': user_json(request.user),
        'bookings': CustomerBookingSerializer(bookings, many=True, context={'request': request}).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request, pk):
    cancelled, message = customer_cancel(get_object_or_404(BookingRequest, pk=pk, customer=request.user))
    return Response({'message': message}) if cancelled else error(message)


class LoginEndpoint(FormEndpoint):
    """Takes ?next= (or a "next" field) like the Django login page."""

    def get_form(self, data=None, files=None):
        return EmailLoginForm(self.request._request, data=data)

    def describe(self, form):
        user = self.request.user
        return {**super().describe(form), 'redirect': safe_next(self.request, home_for(user)) if user.is_authenticated else None}

    def save(self, form):
        login(self.request._request, form.get_user())
        return {'redirect': safe_next(self.request, home_for(form.get_user()))}


@api_view(['POST'])
def logout_view(request):
    logout(request._request)
    return Response({'redirect': reverse('index')})


class SignUpEndpoint(FormEndpoint):
    form_class = SignUpForm

    def describe(self, form):
        user = self.request.user
        return {**super().describe(form), 'redirect': home_for(user) if user.is_authenticated else None}

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response({'redirect': home_for(request.user)})
        return super().post(request, *args, **kwargs)

    def save(self, form):
        user = form.save()
        login(self.request._request, user, backend='django.contrib.auth.backends.ModelBackend')
        return {'message': welcome_message(user), 'redirect': safe_next(self.request, reverse('account'))}


class PasswordResetEndpoint(FormEndpoint):
    form_class = StyledPasswordResetForm

    def save(self, form):
        # The link in the email uses the address the request came to, so it opens the frontend
        form.save(request=self.request._request, use_https=self.request.is_secure())
        return {'redirect': reverse('password_reset_done')}


def reset_link_user(uidb64, token):
    """The user a password reset (or chef invite) link is for, or None if it has expired or was used."""
    try:
        user = User._default_manager.get(pk=urlsafe_base64_decode(uidb64).decode())
    except (TypeError, ValueError, OverflowError, User.DoesNotExist, ValidationError):
        return None
    return user if default_token_generator.check_token(user, token) else None


class SetPasswordEndpoint(FormEndpoint):
    """The "choose a password" link from a password reset or chef invite email."""

    def load(self):
        self.user = reset_link_user(self.kwargs['uidb64'], self.kwargs['token'])

    def get_form(self, data=None, files=None):
        return StyledSetPasswordForm(self.user, data)

    def describe(self, form):
        return {**super().describe(form), 'validlink': self.user is not None,
                'username': self.user.username if self.user else ''}

    def post(self, request, *args, **kwargs):
        if self.user is None:
            return error('This link has expired or was already used. Request a new one.')
        return super().post(request, *args, **kwargs)

    def save(self, form):
        form.save()
        return {'redirect': reverse('password_reset_complete')}

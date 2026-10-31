"""Chef logins. Chefs don't sign up themselves: the team approves their application and invites them.

Used by both the Django admin and the mobile team pages, so they behave the same.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from . import notifications
from .models import Chef, ChefApplication, ChefPhoto, City, ServiceCategory

User = get_user_model()

# Which marketplace services an applicant gets, based on what they said they offer
APPLICATION_SERVICE_SLUGS = {
    ChefApplication.Services.MEALS: ['home-cooked-meals'],
    ChefApplication.Services.PRIVATE: ['private-chefs'],
    ChefApplication.Services.BOTH: ['home-cooked-meals', 'private-chefs'],
}


def set_password_path(user):
    """Path of the one-time "choose a password" page for this user."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return reverse('password_reset_confirm', args=[uid, default_token_generator.make_token(user)])


def invite_chef(chef, approved=False, message=''):
    """Give the chef a login (username = their email) and email them a link to choose a password.

    Safe to run again: it reuses the chef's login and just sends a fresh link.
    """
    user = chef.user
    if user is None:
        email = chef.email.strip().lower()
        user = User.objects.filter(username__iexact=email).first()
        if user is None:
            user = User(username=email, email=email)
        elif hasattr(user, 'chef_profile'):
            raise ValueError(f'{email} is already the login of {user.chef_profile.name}.')
        user.first_name, _, user.last_name = chef.name.removeprefix('Chef ').partition(' ')
        # A random password stops anyone who signed up with this email before us from getting
        # into the chef's dashboard. Only the inbox owner can use the link we send.
        user.set_password(get_random_string(40))
        user.save()
        chef.user = user
        chef.save(update_fields=['user'])

    notifications.chef_invite(chef, set_password_path(user), approved=approved, message=message)
    return user


def create_chef_profile(application):
    """A hidden marketplace profile from an application. The chef adds a photo, packages and prices after logging in."""
    city = next(
        (c for c in City.objects.all() if c.name.lower() in application.location.lower()),
        City.objects.first(),
    )
    with transaction.atomic():
        chef = Chef.objects.create(
            application=application,
            name=f'Chef {application.full_name.split()[0]}',
            headline=f'{application.get_cuisine_display()} by {application.full_name}',
            bio=application.bio,
            cuisine=application.cuisine,
            city=city,
            area=application.location,
            years_experience=application.years_experience,
            starting_price=0,
            phone=application.phone,
            email=application.email,
            national_id=application.national_id.name,
            food_handler_certificate=application.food_handler_certificate.name,
            is_active=False,
            is_verified=True,
        )
        chef.services.set(ServiceCategory.objects.filter(slug__in=APPLICATION_SERVICE_SLUGS[application.services]))
        for dish in application.dish_photos.all():
            ChefPhoto.objects.create(chef=chef, image=dish.image.name)
    return chef


def approve_application(application, message=''):
    """Approve, create the chef's hidden profile and email them a welcome (with `message`) and their login link.

    Raises ValueError if the login could not be sent (the application is still approved).
    """
    application.status = ChefApplication.Status.APPROVED
    application.reviewed_at = timezone.now()
    application.decision_message = message.strip()
    application.save(update_fields=['status', 'reviewed_at', 'decision_message'])
    chef = getattr(application, 'chef', None) or create_chef_profile(application)
    invite_chef(chef, approved=True, message=application.decision_message)
    return chef


def reject_application(application, reason=''):
    application.status = ChefApplication.Status.REJECTED
    application.reviewed_at = timezone.now()
    application.decision_message = reason.strip()
    application.save(update_fields=['status', 'reviewed_at', 'decision_message'])
    notifications.application_rejected(application, application.decision_message)

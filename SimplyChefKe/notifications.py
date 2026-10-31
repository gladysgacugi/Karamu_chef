"""Alerts for new bookings and chef applications, by email and WhatsApp.

WhatsApp messages are sent from the official business number through the
WhatsApp Cloud API. Until WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID are set,
WhatsApp is skipped and only email goes out.
"""
import json
import logging
import urllib.request

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)

GRAPH_API_URL = 'https://graph.facebook.com/v21.0/{phone_number_id}/messages'


def send_whatsapp(to, text):
    """Send a text message from the business number. Returns True if Meta accepted it."""
    token, phone_number_id = settings.WHATSAPP_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID
    if not (token and phone_number_id and to):
        return False

    payload = {
        'messaging_product': 'whatsapp',
        'to': to.lstrip('+'),
        'type': 'text',
        'text': {'body': text, 'preview_url': True},
    }
    req = urllib.request.Request(
        GRAPH_API_URL.format(phone_number_id=phone_number_id),
        data=json.dumps(payload).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception:
        # A failed alert must never break the customer's booking
        logger.exception('WhatsApp message to %s failed', to)
        return False


def send_email(to, subject, body):
    if not to:
        return
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to] if isinstance(to, str) else to)
    except Exception:
        logger.exception('Email "%s" to %s failed', subject, to)


def notify_team(subject, body):
    send_email(settings.NOTIFY_EMAILS, subject, body)
    send_whatsapp(settings.WHATSAPP_NOTIFY_TO, f'*{subject}*\n\n{body}')


def admin_link(obj):
    return settings.SITE_URL + reverse(f'admin:SimplyChefKe_{obj._meta.model_name}_change', args=[obj.pk])


def team_link(name, *args):
    return settings.SITE_URL + reverse(name, args=args)


def booking_summary(booking):
    return f'{booking.event_date:%A %d %B}, {booking.get_time_slot_display()}'


def booking_created(booking):
    package = booking.package.name if booking.package else 'Custom request'
    notify_team(
        f'New booking for {booking.chef.name}',
        f'Customer: {booking.full_name} ({booking.phone})\n'
        f'Package: {package}\n'
        f'Date: {booking.event_date:%a %d %b %Y}, {booking.get_time_slot_display()}\n'
        f'Guests: {booking.guests}\n'
        f'Location: {booking.location}\n'
        f'Notes: {booking.notes or "-"}\n\n'
        f'Open in admin: {admin_link(booking)}',
    )
    if booking.chef.user_id:
        send_email(
            booking.chef.email,
            f'New booking request from {booking.full_name}',
            f'Hi {booking.chef.name},\n\n'
            f'{booking.full_name} would like to book you for {booking.event_date:%A %d %B} '
            f'({booking.get_time_slot_display()}, {booking.guests} guests) in {booking.location}.\n'
            f'Package: {package}\n'
            f'Notes: {booking.notes or "-"}\n\n'
            f'Confirm or decline it on your dashboard: {settings.SITE_URL}{reverse("chef_dashboard")}\n\n'
            f'Karamu',
        )
    send_email(
        booking.email,
        f'We received your booking request - {booking.chef.name}',
        f'Hi {booking.full_name.split()[0]},\n\n'
        f'Thanks for booking {booking.chef.name} for {booking.event_date:%A %d %B} '
        f'({booking.get_time_slot_display()}, {booking.guests} guests).\n\n'
        f"Once the chef confirms we'll email you the price and how to pay by M-Pesa. Nothing is charged before that.\n"
        f'Track your booking: {settings.SITE_URL}{booking.customer_url()}\n\n'
        f'Questions? WhatsApp us: {settings.WHATSAPP_URL}\n\n'
        f'Karamu',
    )


BOOKING_STATUS_MESSAGES = {
    'confirmed': 'Good news - {chef} has confirmed your booking.',
    'cancelled': "Sorry - {chef} can't make it. Reply on WhatsApp and we'll help you find another chef.",
    'completed': 'We hope you enjoyed the food! Tell others how it went by leaving {chef} a review: {review_url}',
}


def customer_status_message(booking):
    text = BOOKING_STATUS_MESSAGES[booking.status].format(
        chef=booking.chef.name, review_url=settings.SITE_URL + booking.customer_url('booking_review'),
    )
    if booking.status == 'confirmed':
        if booking.price:
            text += (f'\n\nAgreed price: KSh {booking.price:,}\n'
                     f'Pay by M-Pesa here: {settings.SITE_URL}{booking.customer_url("booking_checkout")}')
        else:
            text += " We'll send you the price and M-Pesa payment details shortly."
    elif booking.status == 'cancelled' and booking.payment_status == 'paid':
        text += f'\n\nYou have already paid KSh {booking.price:,}. We will refund you by M-Pesa.'
    return text


def booking_status_changed(booking, by_team=False):
    """A booking was confirmed, declined or completed, by the chef or by the team on their behalf."""
    if by_team:
        # Let the chef know the team updated their booking
        if booking.chef.user_id:
            send_email(
                booking.chef.email,
                f'Booking {booking.get_status_display().lower()}: {booking.full_name}',
                f'Hi {booking.chef.name},\n\n'
                f'The Karamu team marked your booking with {booking.full_name} on '
                f'{booking.event_date:%A %d %B} ({booking.get_time_slot_display()}) as '
                f'{booking.get_status_display().lower()}.\n\n'
                f'See your bookings: {settings.SITE_URL}{reverse("chef_dashboard")}\n\n'
                f'Karamu',
            )
    else:
        refund = (f'\nThe customer has already paid KSh {booking.price:,} - refund them.'
                  if booking.status == 'cancelled' and booking.payment_status == 'paid' else '')
        notify_team(
            f'{booking.chef.name} marked a booking {booking.get_status_display().lower()}',
            f'Customer: {booking.full_name} ({booking.phone})\n'
            f'Date: {booking.event_date:%a %d %b %Y}, {booking.get_time_slot_display()}\n'
            f'Price: {f"KSh {booking.price:,}" if booking.price else "-"}{refund}\n\n'
            f'Open: {team_link("team_booking", booking.pk)}',
        )
    send_email(
        booking.email,
        f'Your booking with {booking.chef.name} is {booking.get_status_display().lower()}',
        f'Hi {booking.full_name.split()[0]},\n\n'
        + customer_status_message(booking)
        + f'\n\nBooking: {booking_summary(booking)}\n'
        f'Questions? WhatsApp us: {settings.WHATSAPP_URL}\n\n'
        f'Karamu',
    )


def payment_submitted(booking):
    notify_team(
        f'Check M-Pesa payment for booking {booking.payment_reference}',
        f'Customer: {booking.full_name} ({booking.phone})\n'
        f'Chef: {booking.chef.name}, {booking_summary(booking)}\n'
        f'Amount due: KSh {booking.price:,}\n'
        f'M-Pesa code: {booking.mpesa_code}\n\n'
        f'Check it on the M-Pesa statement, then mark it paid: {team_link("team_booking", booking.pk)}',
    )


def payment_status_changed(booking):
    """The team checked a payment: paid, not found (back to unpaid) or refunded."""
    first_name = booking.full_name.split()[0]
    sign_off = f'\n\nQuestions? WhatsApp us: {settings.WHATSAPP_URL}\n\nKaramu'
    if booking.payment_status == 'paid':
        send_email(
            booking.email,
            f'Payment received - {booking.chef.name} on {booking.event_date:%d %b}',
            f'Hi {first_name},\n\n'
            f'We have received your payment of KSh {booking.price:,} (M-Pesa {booking.mpesa_code or "-"}). '
            f'Your booking is all set.\n\n'
            f'Chef: {booking.chef.name}\nWhen: {booking_summary(booking)}\nWhere: {booking.location}\n'
            f'Booking reference: {booking.payment_reference}' + sign_off,
        )
        if booking.chef.user_id:
            send_email(
                booking.chef.email,
                f'Paid: {booking.full_name} on {booking.event_date:%d %b}',
                f'Hi {booking.chef.name},\n\n'
                f'{booking.full_name} has paid for their booking on {booking_summary(booking)} '
                f'({booking.guests} guests, {booking.location}). Customer phone: {booking.phone}\n\n'
                f'See your bookings: {settings.SITE_URL}{reverse("chef_dashboard")}\n\nKaramu',
            )
    elif booking.payment_status == 'unpaid':
        send_email(
            booking.email,
            f'We could not find your payment - booking {booking.payment_reference}',
            f'Hi {first_name},\n\n'
            f"We couldn't match the M-Pesa code you sent to a payment for this booking. "
            f'Please check the code in your M-Pesa SMS and enter it again: '
            f'{settings.SITE_URL}{booking.customer_url("booking_checkout")}' + sign_off,
        )
    elif booking.payment_status == 'refunded':
        send_email(
            booking.email,
            f'Refund sent - booking {booking.payment_reference}',
            f'Hi {first_name},\n\nWe have refunded your payment of KSh {booking.price:,} to {booking.phone} by M-Pesa.'
            + sign_off,
        )


def booking_reminder(booking):
    """Sent the day before a confirmed booking."""
    send_email(
        booking.email,
        f'Tomorrow: {booking.chef.name} is cooking for you',
        f'Hi {booking.full_name.split()[0]},\n\n'
        f'A reminder that {booking.chef.name} is booked for {booking_summary(booking)} '
        f'at {booking.location} ({booking.guests} guests).\n'
        + (f'\nYou have not paid yet. Pay KSh {booking.price:,} by M-Pesa here: '
           f'{settings.SITE_URL}{booking.customer_url("booking_checkout")}\n'
           if booking.price and booking.payment_status == 'unpaid' else '')
        + f'\nQuestions? WhatsApp us: {settings.WHATSAPP_URL}\n\nKaramu',
    )
    if booking.chef.user_id:
        send_email(
            booking.chef.email,
            f'Tomorrow: {booking.full_name}, {booking.get_time_slot_display()}',
            f'Hi {booking.chef.name},\n\n'
            f'A reminder that you are cooking for {booking.full_name} on {booking_summary(booking)}.\n'
            f'Where: {booking.location}\nGuests: {booking.guests}\n'
            f'Package: {booking.package.name if booking.package else "Custom request"}\n'
            f'Requests: {booking.notes or "-"}\n'
            f'Customer phone: {booking.phone}\n'
            f'Payment: {booking.get_payment_status_display()}\n\n'
            f'Karamu',
        )


def review_created(review):
    notify_team(
        f'New {review.rating}-star review for {review.chef.name}',
        f'From: {review.customer_name}\n\n{review.comment}\n\n'
        f'Publish or decline it: {team_link("team_reviews")}',
    )


def review_published(review):
    if review.chef.user_id:
        send_email(
            review.chef.email,
            f'New {review.rating}-star review on your profile',
            f'Hi {review.chef.name},\n\n'
            f'{review.customer_name} reviewed you:\n\n"{review.comment}"\n\n'
            f'See it on your profile: {settings.SITE_URL}{review.chef.get_absolute_url()}#reviews\n\nKaramu',
        )


def booking_cancelled_by_customer(booking):
    body = (
        f'{booking.full_name} cancelled their request for {booking.event_date:%a %d %b %Y}, '
        f'{booking.get_time_slot_display()}.'
    )
    notify_team(f'Booking cancelled by customer - {booking.chef.name}', f'{body}\n\nOpen in admin: {admin_link(booking)}')
    if booking.chef.user_id:
        send_email(booking.chef.email, f'Booking cancelled by {booking.full_name}', f'Hi {booking.chef.name},\n\n{body}\n\nKaramu')


def booking_message_sent(message):
    """Email a booking message to the other side: the customer if the chef wrote it, otherwise the chef."""
    booking = message.booking
    if message.from_chef:
        send_email(
            booking.email,
            f'New message from {booking.chef.name} about your booking',
            f'Hi {booking.full_name.split()[0]},\n\n'
            f'{booking.chef.name} wrote about your booking on {booking_summary(booking)}:\n\n'
            f'"{message.body}"\n\n'
            f'Reply here: {settings.SITE_URL}{booking.customer_url()}#messages\n\n'
            f'Karamu',
        )
    elif booking.chef.user_id:
        send_email(
            booking.chef.email,
            f'New message from {booking.full_name}',
            f'Hi {booking.chef.name},\n\n'
            f'{booking.full_name} wrote about their booking on {booking_summary(booking)}:\n\n'
            f'"{message.body}"\n\n'
            f'Reply here: {settings.SITE_URL}{reverse("chef_booking", args=[booking.pk])}#messages\n\n'
            f'Karamu',
        )


def chef_documents_updated(chef):
    notify_team(
        f'{chef.name} uploaded new documents',
        f'{chef.name} replaced their ID or food handler\'s certificate, so their "verified" badge is off until you check them.\n\n'
        f'Check them: {team_link("team_chefs")}?show=documents',
    )


def chef_invite(chef, set_password_path, approved=False, message=''):
    """The chef's login link. `approved` makes it the welcome email sent when their application is approved,
    with the team's own `message` to them."""
    if approved:
        subject = "You're approved - welcome to Karamu!"
        intro = (
            'Congratulations! Your application to cook with Karamu has been approved and your chef account is ready.\n\n'
            + (f'{message.strip()}\n\n' if message.strip() else '')
            + 'Choose a password here (the link works for 3 days):\n'
        )
        outro = ('Add a good photo of yourself, your packages and prices. Once your profile is complete '
                 "we'll put it live on the marketplace so customers can book you.\n\n")
    else:
        subject = 'Your Karamu chef account'
        intro = 'Your chef account is ready. Choose a password here (the link works for 3 days):\n'
        outro = ''
    send_email(
        chef.email,
        subject,
        f'Hi {chef.name},\n\n'
        f'{intro}'
        f'{settings.SITE_URL}{set_password_path}\n\n'
        f'Then log in with {chef.user.username} to update your profile, menu, prices and photos, '
        f'and to confirm your bookings: {settings.SITE_URL}{reverse("login")}\n\n'
        f'{outro}'
        f'Link expired? Use "Forgot password" on the login page.\n\n'
        f'Karamu',
    )


def application_rejected(application, reason=''):
    send_email(
        application.email,
        'Your Karamu application',
        f'Hi {application.full_name.split()[0]},\n\n'
        f'Thank you for applying to cook with Karamu. After reviewing your application, '
        f"we're not able to take you on as a chef at this time.\n\n"
        + (f'Reason: {reason.strip()}\n\n' if reason.strip() else '')
        + f"You're welcome to apply again in future. Questions? WhatsApp us: {settings.WHATSAPP_URL}\n\n"
        f'Karamu',
    )


def match_request_created(match):
    notify_team(
        f'Find a chef for {match.full_name}',
        f'Customer: {match.full_name} ({match.phone})\n'
        f'Occasion: {match.get_occasion_display()}, {match.get_guests_display()}\n'
        f'Cuisine: {match.get_cuisine_display() or "Chef decides"}\n'
        f'Date: {match.event_date:%a %d %b %Y}, {match.get_time_slot_display()}\n'
        f'Location: {match.location}\n'
        f'Notes: {match.notes or "-"}\n\n'
        f'Open in admin: {admin_link(match)}',
    )
    send_email(
        match.email,
        'We received your chef request',
        f'Hi {match.full_name.split()[0]},\n\n'
        f'Thanks for your {match.get_occasion_display().lower()} request for {match.event_date:%A %d %B} '
        f'({match.get_time_slot_display()}, {match.get_guests_display().lower()}).\n\n'
        f"We're finding the right chef for you and will be in touch shortly.\n"
        f'Questions? WhatsApp us: {settings.WHATSAPP_URL}\n\n'
        f'Karamu',
    )


def contact_message_created(msg):
    notify_team(
        f'Contact form: {msg.get_subject_display()} from {msg.name}',
        f'From: {msg.name} <{msg.email}>{f" ({msg.phone})" if msg.phone else ""}\n\n'
        f'{msg.message}\n\n'
        f'Open in admin: {admin_link(msg)}',
    )


def application_created(application):
    notify_team(
        f'New chef application: {application.full_name}',
        f'Phone: {application.phone}\n'
        f'Email: {application.email}\n'
        f'Location: {application.location}\n'
        f'{application.get_chef_type_display()} - {application.get_cuisine_display()}, '
        f'{application.years_experience} yrs\n'
        f'Services: {application.get_services_display()}\n\n'
        f'Review it: {admin_link(application)}',
    )
    send_email(
        application.email,
        'Your Karamu application',
        f'Hi {application.full_name.split()[0]},\n\n'
        f"Thanks for applying to cook with Karamu. We'll review your details and documents "
        f'and get back to you within 3 working days.\n\n'
        f'Questions? WhatsApp us: {settings.WHATSAPP_URL}\n\n'
        f'Karamu',
    )

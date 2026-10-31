import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from SimplyChefKe import notifications
from SimplyChefKe.models import BookingRequest


class Command(BaseCommand):
    help = ("Emails customers and chefs the day before a confirmed booking. Run once a day, e.g. at 9 AM. "
            "Safe to run more than once: each booking is only reminded once.")

    def handle(self, *args, **options):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        bookings = BookingRequest.objects.filter(
            status=BookingRequest.Status.CONFIRMED, event_date=tomorrow, reminder_sent_at__isnull=True,
        ).select_related('chef', 'package')

        sent = 0
        for booking in bookings:
            notifications.booking_reminder(booking)
            booking.reminder_sent_at = timezone.now()
            booking.save(update_fields=['reminder_sent_at'])
            sent += 1
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} reminder(s) for {tomorrow:%a %d %b}.'))

import datetime

from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Avg, Count, Q
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import slugify


MAX_UPLOAD_MB = 5

# Signs the booking links in customer emails
BOOKING_KEY_SALT = 'booking-access'

kenyan_phone_validator = RegexValidator(
    regex=r'^(?:\+254|254|0)(7|1)\d{8}$',
    message='Enter a valid Kenyan number, e.g. 0712345678 or +254712345678.',
)

mpesa_code_validator = RegexValidator(
    regex=r'^[A-Z0-9]{10}$',
    message='An M-Pesa code is 10 letters and numbers, e.g. SJK4H7L2QP.',
)


def validate_file_size(file):
    if file.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f'File must be smaller than {MAX_UPLOAD_MB} MB.')


DOCUMENT_VALIDATORS = [FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png']), validate_file_size]


class ChefApplication(models.Model):
    """A request from a chef or home cook to join Karamu."""

    class ChefType(models.TextChoices):
        PROFESSIONAL = 'professional', 'Professional Chef'
        HOME_COOK = 'home_cook', 'Home Cook'

    class Services(models.TextChoices):
        MEALS = 'meals', 'Sell home-cooked meals'
        PRIVATE = 'private', 'Private chef & events'
        BOTH = 'both', 'Both'

    class Cuisine(models.TextChoices):
        KENYAN = 'kenyan', 'Kenyan Home Classics'
        GRILLS = 'grills', 'Nyama Choma & Grills'
        COASTAL = 'coastal', 'Swahili / Coastal'
        BAKING = 'baking', 'Baking & Pastry'
        CONTINENTAL = 'continental', 'Continental'
        INDIAN = 'indian', 'Indian'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    # Personal details
    full_name = models.CharField(max_length=120)
    phone = models.CharField(
        'Phone (M-Pesa)', max_length=13, validators=[kenyan_phone_validator],
        help_text='Used for contact and M-Pesa payouts.',
    )
    email = models.EmailField()
    location = models.CharField('Location / Estate', max_length=120)

    # Cooking profile
    chef_type = models.CharField(max_length=20, choices=ChefType.choices)
    services = models.CharField('Services offered', max_length=10, choices=Services.choices)
    cuisine = models.CharField('Main cuisine', max_length=20, choices=Cuisine.choices)
    years_experience = models.PositiveSmallIntegerField('Years of experience')
    bio = models.TextField('About you', help_text='Your story, signature dishes and where you have cooked.')

    # Vetting documents
    national_id = models.FileField(
        'National ID (copy)', upload_to='chef_applications/ids/', validators=DOCUMENT_VALIDATORS,
    )
    food_handler_certificate = models.FileField(
        "Food handler's certificate", upload_to='chef_applications/certificates/', validators=DOCUMENT_VALIDATORS,
    )

    agreed_to_terms = models.BooleanField(default=False)

    # Admin review
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    admin_notes = models.TextField(blank=True)
    decision_message = models.TextField(blank=True, help_text='The welcome message or rejection reason we emailed the applicant.')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} ({self.get_status_display()})'


class DishPhoto(models.Model):
    """A photo of a dish submitted with a chef application."""

    application = models.ForeignKey(ChefApplication, on_delete=models.CASCADE, related_name='dish_photos')
    image = models.ImageField(upload_to='chef_applications/dishes/', validators=[validate_file_size])

    def __str__(self):
        return f'Dish photo for {self.application.full_name}'


# ---------------------------------------------------------------------------
# Marketplace
# ---------------------------------------------------------------------------

class ServiceCategory(models.Model):
    """A type of service chefs offer, e.g. Private Chefs or Meal Prep."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=40, default='fa-utensils', help_text='Font Awesome icon class, e.g. fa-utensils.')
    starting_price = models.PositiveIntegerField('Starting price (KSh)')
    price_unit = models.CharField(max_length=30, help_text='e.g. "per event", "per person", "per class".')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'service categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('marketplace')}?service={self.slug}"


class City(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'cities'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('marketplace')}?city={self.slug}"


class ChefQuerySet(models.QuerySet):
    def live(self):
        return self.filter(is_active=True)

    def with_ratings(self):
        published = Q(reviews__status=Review.Status.PUBLISHED)
        return self.annotate(
            avg_rating=Avg('reviews__rating', filter=published),
            review_count=Count('reviews', filter=published),
        )


class Chef(models.Model):
    """A chef's public profile on the marketplace."""

    application = models.OneToOneField(
        ChefApplication, on_delete=models.SET_NULL, null=True, blank=True, related_name='chef',
        help_text='The application this profile was created from.',
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='chef_profile',
        help_text='The login this chef uses to manage their profile and bookings.',
    )
    name =models.CharField('Display name', max_length=120, help_text='e.g. "Chef Wanjiru".')
    slug = models.SlugField(unique=True, blank=True)
    headline = models.CharField(max_length=140, help_text='One line shown on cards, e.g. "Kenyan home classics for families".')
    bio = models.TextField()
    photo = models.ImageField(upload_to='chefs/photos/', blank=True, validators=[validate_file_size])
    cover_image = models.ImageField(upload_to='chefs/covers/', blank=True, validators=[validate_file_size])

    services = models.ManyToManyField(ServiceCategory, related_name='chefs')
    cuisine = models.CharField('Main cuisine', max_length=20, choices=ChefApplication.Cuisine.choices)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='chefs')
    area = models.CharField('Area / Estate', max_length=120, blank=True)
    years_experience = models.PositiveSmallIntegerField(default=0)

    starting_price = models.PositiveIntegerField('Starting price (KSh)')
    price_unit = models.CharField(max_length=30, default='per event')

    phone = models.CharField(max_length=13, validators=[kenyan_phone_validator])
    email = models.EmailField()

    # Vetting documents, copied from the application and replaceable by the chef. Private to the chef and the team.
    national_id = models.FileField(
        'National ID (copy)', upload_to='chefs/documents/ids/', blank=True, validators=DOCUMENT_VALIDATORS,
    )
    food_handler_certificate = models.FileField(
        "Food handler's certificate", upload_to='chefs/documents/certificates/', blank=True,
        validators=DOCUMENT_VALIDATORS,
    )
    documents_updated_at = models.DateTimeField(
        null=True, blank=True, help_text='When the chef last replaced a document. Check it, then tick "verified" again.',
    )

    is_active = models.BooleanField('Live on marketplace', default=True)
    is_accepting_bookings = models.BooleanField(
        'Taking new bookings', default=True,
        help_text='Chefs untick this to pause new requests without hiding their profile.',
    )
    is_verified = models.BooleanField('ID & certificate verified', default=False)
    is_featured = models.BooleanField('Show on homepage', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ChefQuerySet.as_manager()

    class Meta:
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'chef'
            slug, n = base, 2
            while Chef.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f'{base}-{n}', n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('chef_detail', args=[self.slug])

    @property
    def photo_url(self):
        return self.photo.url if self.photo else static('img/chefs/1.jpg')

    @property
    def cover_url(self):
        return self.cover_image.url if self.cover_image else static('img/banner-img.jpg')

    def is_away(self, date):
        return self.time_off.filter(start_date__lte=date, end_date__gte=date).exists()

    def slot_taken(self, date, time_slot, exclude=None):
        """True if the chef already has a confirmed booking at that date and time."""
        clashes = self.bookings.filter(event_date=date, time_slot=time_slot, status=BookingRequest.Status.CONFIRMED)
        if exclude is not None:
            clashes = clashes.exclude(pk=exclude.pk)
        return clashes.exists()

    def upcoming_time_off(self):
        return self.time_off.filter(end_date__gte=datetime.date.today())


class ChefTimeOff(models.Model):
    """Days a chef can't take bookings, e.g. travel or a week already full of events."""

    chef = models.ForeignKey(Chef, on_delete=models.CASCADE, related_name='time_off')
    start_date = models.DateField('From')
    end_date = models.DateField('To')
    note = models.CharField(max_length=100, blank=True, help_text='Private, e.g. "Family wedding".')

    class Meta:
        ordering = ['start_date']
        verbose_name_plural = 'time off'

    def __str__(self):
        return f'{self.chef.name} away {self.start_date} - {self.end_date}'

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'The last day must be on or after the first day.'})


class ChefPackage(models.Model):
    """A bookable offer on a chef's profile, e.g. "Private dinner for 6"."""

    chef = models.ForeignKey(Chef, on_delete=models.CASCADE, related_name='packages')
    service = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(help_text='What is included - dishes, courses, shopping, clean-up...')
    price = models.PositiveIntegerField('Price (KSh)')
    price_unit = models.CharField(max_length=30, default='per event')
    is_active = models.BooleanField('Offered', default=True, help_text='Untick to hide this package without deleting it.')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'price']

    def __str__(self):
        return f'{self.chef.name} - {self.name}'

    def price_for(self, guests):
        """The package price for this many guests, for packages priced per person."""
        unit = self.price_unit.lower()
        return self.price * guests if 'person' in unit or 'guest' in unit else self.price


class ChefPhoto(models.Model):
    chef = models.ForeignKey(Chef, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='chefs/gallery/', validators=[validate_file_size])
    caption = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.caption or f'Photo of {self.chef.name}'


class Review(models.Model):
    """Customer review of a completed booking. Hidden until the team publishes it."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'To check'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Declined'

    chef = models.ForeignKey(Chef, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(
        'BookingRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='review',
        help_text='The completed booking this review is about.',
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews',
    )
    customer_name = models.CharField(max_length=80)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rating}/5 for {self.chef.name} by {self.customer_name}'


class BookingRequest(models.Model):
    """A customer's request to book a chef. The chef confirms and sets the price, then the customer pays by M-Pesa."""

    class TimeSlot(models.TextChoices):
        BREAKFAST = 'breakfast', 'Breakfast (7 - 10 AM)'
        LUNCH = 'lunch', 'Lunch (12 - 2 PM)'
        AFTERNOON = 'afternoon', 'Afternoon (3 - 5 PM)'
        DINNER = 'dinner', 'Dinner (6 - 9 PM)'

    class Status(models.TextChoices):
        NEW = 'new', 'New'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', 'Not paid'
        SUBMITTED = 'submitted', 'Checking payment'
        PAID = 'paid', 'Paid'
        REFUNDED = 'refunded', 'Refunded'

    # What a chef can move a booking to from each status
    CHEF_TRANSITIONS = {
        Status.NEW: [Status.CONFIRMED, Status.CANCELLED],
        Status.CONFIRMED: [Status.COMPLETED, Status.CANCELLED],
    }

    chef = models.ForeignKey(Chef, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings',
        help_text='Set when the booking was made while logged in.',
    )
    package = models.ForeignKey(ChefPackage, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField('Phone (M-Pesa)', max_length=13, validators=[kenyan_phone_validator])
    email = models.EmailField(blank=True)
    event_date = models.DateField()
    time_slot = models.CharField(max_length=10, choices=TimeSlot.choices)
    guests = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    location = models.CharField('Location / Estate', max_length=150)
    notes = models.TextField('Special requests', blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)

    # Payment
    price = models.PositiveIntegerField(
        'Agreed price (KSh)', null=True, blank=True, help_text='Set when the booking is confirmed. This is what the customer pays.',
    )
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    mpesa_code = models.CharField('M-Pesa code', max_length=10, blank=True, validators=[mpesa_code_validator])
    paid_at = models.DateTimeField(null=True, blank=True)

    team_notes = models.TextField(blank=True, help_text='Private to the team.')
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # One M-Pesa payment can't be used for two bookings
            models.UniqueConstraint(fields=['mpesa_code'], condition=~Q(mpesa_code=''), name='unique_mpesa_code'),
        ]

    def __str__(self):
        return f'{self.full_name} -> {self.chef.name} on {self.event_date}'

    @property
    def chef_next_statuses(self):
        return [self.Status(s) for s in self.CHEF_TRANSITIONS.get(self.status, [])]

    @property
    def customer_can_cancel(self):
        return self.status == self.Status.NEW

    @property
    def payment_reference(self):
        """The M-Pesa account number the customer enters, so the team can match the payment."""
        return f'SC{self.pk}'

    @property
    def suggested_price(self):
        return self.package.price_for(self.guests) if self.package else None

    @property
    def customer_can_pay(self):
        return self.status == self.Status.CONFIRMED and self.payment_status == self.PaymentStatus.UNPAID and bool(self.price)

    @property
    def team_payment_actions(self):
        """The payment statuses the team can move this booking to."""
        if self.payment_status == self.PaymentStatus.SUBMITTED:
            return [self.PaymentStatus.PAID, self.PaymentStatus.UNPAID]
        if self.payment_status == self.PaymentStatus.UNPAID and self.price and self.status != self.Status.CANCELLED:
            return [self.PaymentStatus.PAID]
        if self.payment_status == self.PaymentStatus.PAID and self.status == self.Status.CANCELLED:
            return [self.PaymentStatus.REFUNDED]
        return []

    @property
    def can_be_reviewed(self):
        return self.status == self.Status.COMPLETED and not hasattr(self, 'review')

    def customer_url(self, name='booking_confirmation'):
        """A link to one of the customer's booking pages that works without logging in, for emails."""
        return f"{reverse(name, args=[self.pk])}?key={signing.dumps(self.pk, salt=BOOKING_KEY_SALT)}"

    @classmethod
    def pk_from_key(cls, key):
        try:
            return signing.loads(key, salt=BOOKING_KEY_SALT)
        except signing.BadSignature:
            return None


class BookingMessage(models.Model):
    """A message between the chef and the customer about a booking. Each one is emailed to the other side."""

    booking = models.ForeignKey(BookingRequest, on_delete=models.CASCADE, related_name='messages')
    from_chef = models.BooleanField(help_text='False means the customer sent it.')
    body = models.TextField('Message', max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{"Chef" if self.from_chef else "Customer"} on booking {self.booking_id}: {self.body[:40]}'


# ---------------------------------------------------------------------------
# Homepage enquiries
# ---------------------------------------------------------------------------

class ChefMatchRequest(models.Model):
    """'Book a Private Chef' on the homepage: the customer hasn't picked a chef, so the team matches one."""

    class Occasion(models.TextChoices):
        DINNER = 'dinner', 'Private Dinner'
        PARTY = 'party', 'Birthday / Party'
        CORPORATE = 'corporate', 'Corporate Event'
        WEDDING = 'wedding', 'Wedding / Ruracio'
        MEAL_PREP = 'meal_prep', 'Weekly Meal Prep'
        CLASS = 'class', 'Cooking Class'

    class Guests(models.TextChoices):
        UP_TO_2 = '1-2', '1 - 2 Guests'
        UP_TO_6 = '3-6', '3 - 6 Guests'
        UP_TO_15 = '7-15', '7 - 15 Guests'
        UP_TO_30 = '16-30', '16 - 30 Guests'
        UP_TO_50 = '31-50', '31 - 50 Guests'
        OVER_50 = '50+', '50+ Guests'

    class Status(models.TextChoices):
        NEW = 'new', 'New'
        MATCHED = 'matched', 'Matched with a chef'
        CLOSED = 'closed', 'Closed'

    full_name = models.CharField(max_length=120)
    phone = models.CharField('Phone (M-Pesa)', max_length=13, validators=[kenyan_phone_validator])
    email = models.EmailField(blank=True)
    occasion = models.CharField(max_length=20, choices=Occasion.choices)
    guests = models.CharField('Number of guests', max_length=10, choices=Guests.choices)
    cuisine = models.CharField(
        'Preferred cuisine', max_length=20, choices=ChefApplication.Cuisine.choices, blank=True,
        help_text='Blank means the chef can decide.',
    )
    event_date = models.DateField('Date')
    time_slot = models.CharField('Time', max_length=10, choices=BookingRequest.TimeSlot.choices)
    location = models.CharField('Location / Estate', max_length=150)
    notes = models.TextField('Special requests', blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    matched_booking = models.ForeignKey(
        BookingRequest, on_delete=models.SET_NULL, null=True, blank=True,
        help_text='The booking created once a chef was found.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.get_occasion_display()} on {self.event_date}'


class ContactMessage(models.Model):
    class Subject(models.TextChoices):
        GENERAL = 'general', 'General Inquiry'
        CHEF = 'chef', 'I Want to Join as a Chef'
        EVENTS = 'events', 'Events & Catering'
        SUPPORT = 'support', 'Order Support'
        PARTNERSHIP = 'partnership', 'Corporate Partnership'
        FEEDBACK = 'feedback', 'Feedback'

    name = models.CharField('Your name', max_length=120)
    email = models.EmailField('Email address')
    phone = models.CharField('Phone number', max_length=13, blank=True, validators=[kenyan_phone_validator])
    subject = models.CharField(max_length=20, choices=Subject.choices)
    message = models.TextField()
    is_handled = models.BooleanField('Replied', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}: {self.get_subject_display()}'


class Subscriber(models.Model):
    """Newsletter sign-up."""

    email = models.EmailField(unique=True)
    is_active = models.BooleanField('Subscribed', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email

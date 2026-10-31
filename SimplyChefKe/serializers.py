"""JSON shapes for the API. The public ones show only what the customer-facing pages already show - never chef contact
details. The chef dashboard and team ones (further down) are only sent to that chef or to staff."""

from rest_framework import serializers

from .models import (
    BookingMessage, BookingRequest, Chef, ChefApplication, ChefMatchRequest, ChefPackage, ChefPhoto, ChefTimeOff, City,
    ContactMessage, Review, ServiceCategory,
)


class AbsoluteUrlField(serializers.CharField):
    """A site-relative URL (e.g. a photo) made absolute, so a separate frontend server can load it."""

    def to_representation(self, value):
        request = self.context.get('request')
        return request.build_absolute_uri(value) if request else value


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['slug', 'name', 'description', 'icon', 'starting_price', 'price_unit']


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['slug', 'name']


class ChefCardSerializer(serializers.ModelSerializer):
    """A chef as shown on marketplace cards."""

    city = CitySerializer()
    services = ServiceSerializer(many=True)
    cuisine = serializers.CharField(source='get_cuisine_display')
    photo = AbsoluteUrlField(source='photo_url')
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.IntegerField()

    class Meta:
        model = Chef
        fields = [
            'slug', 'name', 'headline', 'photo', 'cuisine', 'city', 'area', 'services', 'years_experience',
            'starting_price', 'price_unit', 'is_verified', 'is_featured', 'is_accepting_bookings',
            'avg_rating', 'review_count',
        ]

    def get_avg_rating(self, chef):
        return round(chef.avg_rating, 1) if chef.avg_rating is not None else None


class PackageSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(allow_null=True)

    class Meta:
        model = ChefPackage
        fields = ['id', 'name', 'description', 'price', 'price_unit', 'service']


class PackageWithChefSerializer(PackageSerializer):
    """A package listed on its own (e.g. the homepage), with the chef it belongs to."""

    chef = serializers.SerializerMethodField()

    class Meta(PackageSerializer.Meta):
        fields = PackageSerializer.Meta.fields + ['chef']

    def get_chef(self, package):
        chef = package.chef
        return {
            'slug': chef.slug, 'name': chef.name, 'city': chef.city.name, 'is_verified': chef.is_verified,
            'photo': self.context['request'].build_absolute_uri(chef.photo_url),
        }


class ChefPhotoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ChefPhoto
        fields = ['image', 'caption']

    def get_image(self, photo):
        return self.context['request'].build_absolute_uri(photo.image.url)


class ChefDetailSerializer(ChefCardSerializer):
    """A chef's full public profile."""

    cover = AbsoluteUrlField(source='cover_url')
    packages = PackageSerializer(many=True)
    photos = ChefPhotoSerializer(many=True)
    time_off = serializers.SerializerMethodField()

    class Meta(ChefCardSerializer.Meta):
        # is_active is only ever False for a chef previewing their own profile
        fields = ChefCardSerializer.Meta.fields + ['bio', 'cover', 'packages', 'photos', 'time_off', 'is_active']

    def get_time_off(self, chef):
        # Dates only - the note is private to the chef
        return [{'start_date': t.start_date, 'end_date': t.end_date} for t in chef.upcoming_time_off()[:6]]


class ReviewSerializer(serializers.ModelSerializer):
    chef = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'customer_name', 'rating', 'comment', 'created_at', 'chef']

    def get_chef(self, review):
        return {'slug': review.chef.slug, 'name': review.chef.name}


class BookingMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingMessage
        fields = ['id', 'from_chef', 'body', 'created_at']


class CustomerBookingSerializer(serializers.ModelSerializer):
    """A booking as its customer sees it. Only ever sent to that customer (see views.customer_booking)."""

    chef = serializers.SerializerMethodField()
    package = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display')
    payment_status_display = serializers.CharField(source='get_payment_status_display')
    time_slot_display = serializers.CharField(source='get_time_slot_display')
    review_status = serializers.SerializerMethodField()
    messages = BookingMessageSerializer(many=True, read_only=True)

    class Meta:
        model = BookingRequest
        fields = [
            'id', 'chef', 'package', 'full_name', 'phone', 'email', 'event_date', 'time_slot_display', 'guests',
            'location', 'notes', 'status', 'status_display', 'price', 'payment_status', 'payment_status_display',
            'payment_reference', 'mpesa_code', 'paid_at', 'customer_can_cancel', 'customer_can_pay', 'can_be_reviewed',
            'review_status', 'messages',
        ]

    def get_chef(self, booking):
        chef = booking.chef
        return {'slug': chef.slug, 'name': chef.name, 'photo': self.context['request'].build_absolute_uri(chef.photo_url)}

    def get_package(self, booking):
        package = booking.package
        return {'name': package.name, 'price': package.price, 'price_unit': package.price_unit} if package else None

    def get_review_status(self, booking):
        review = getattr(booking, 'review', None)
        return review.status if review else None


# ---------------------------------------------------------------------------
# Chef dashboard. Uploads are site-relative URLs: the frontend serves /media/ from the same address.
# ---------------------------------------------------------------------------

def file_url(file):
    return file.url if file else ''


class OwnChefSerializer(serializers.ModelSerializer):
    """The logged-in chef, for the top of their dashboard pages."""

    photo = serializers.CharField(source='photo_url')

    class Meta:
        model = Chef
        fields = [
            'name', 'slug', 'photo', 'is_active', 'is_accepting_bookings', 'is_verified', 'documents_updated_at',
        ]


class ChefBookingSerializer(serializers.ModelSerializer):
    """A booking as its chef sees it. The phone number only once the chef has confirmed."""

    package = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    has_email = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display')
    payment_status_display = serializers.CharField(source='get_payment_status_display')
    time_slot_display = serializers.CharField(source='get_time_slot_display')
    next_statuses = serializers.ListField(source='chef_next_statuses', child=serializers.CharField())
    suggested_price = serializers.IntegerField()
    message_count = serializers.IntegerField(required=False)

    class Meta:
        model = BookingRequest
        fields = [
            'id', 'full_name', 'phone', 'has_email', 'event_date', 'time_slot_display', 'guests', 'location', 'notes',
            'package', 'price', 'suggested_price', 'status', 'status_display', 'payment_status',
            'payment_status_display', 'next_statuses', 'created_at', 'message_count',
        ]

    def get_package(self, booking):
        package = booking.package
        return {'name': package.name, 'price': package.price, 'price_unit': package.price_unit} if package else None

    def get_phone(self, booking):
        return booking.phone if booking.status in (BookingRequest.Status.CONFIRMED, BookingRequest.Status.COMPLETED) else ''

    def get_has_email(self, booking):
        return bool(booking.email)


class TimeOffSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChefTimeOff
        fields = ['id', 'start_date', 'end_date', 'note']


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

class TeamBookingSerializer(ChefBookingSerializer):
    """Everything about a booking, for the team."""

    chef = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    team_payment_actions = serializers.ListField(child=serializers.CharField())

    class Meta(ChefBookingSerializer.Meta):
        fields = ChefBookingSerializer.Meta.fields + [
            'chef', 'email', 'customer_email', 'payment_reference', 'mpesa_code', 'paid_at', 'team_notes',
            'reminder_sent_at', 'team_payment_actions',
        ]

    def get_phone(self, booking):
        return booking.phone

    def get_chef(self, booking):
        return {'name': booking.chef.name, 'slug': booking.chef.slug}

    def get_customer_email(self, booking):
        return booking.customer.email if booking.customer else None


class ApplicationSerializer(serializers.ModelSerializer):
    chef_type_display = serializers.CharField(source='get_chef_type_display')
    services_display = serializers.CharField(source='get_services_display')
    cuisine_display = serializers.CharField(source='get_cuisine_display')
    status_display = serializers.CharField(source='get_status_display')

    class Meta:
        model = ChefApplication
        fields = [
            'id', 'full_name', 'phone', 'email', 'location', 'chef_type_display', 'services_display', 'cuisine_display',
            'years_experience', 'bio', 'status', 'status_display', 'admin_notes', 'decision_message', 'created_at',
        ]


class ApplicationDetailSerializer(ApplicationSerializer):
    """An application with its documents, dish photos and the chef profile made from it."""

    national_id = serializers.SerializerMethodField()
    food_handler_certificate = serializers.SerializerMethodField()
    dish_photos = serializers.SerializerMethodField()
    chef = serializers.SerializerMethodField()

    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + ['national_id', 'food_handler_certificate', 'dish_photos', 'chef']

    def get_national_id(self, application):
        return file_url(application.national_id)

    def get_food_handler_certificate(self, application):
        return file_url(application.food_handler_certificate)

    def get_dish_photos(self, application):
        return [photo.image.url for photo in application.dish_photos.all()]

    def get_chef(self, application):
        chef = getattr(application, 'chef', None)
        if chef is None:
            return None
        return {'id': chef.pk, 'name': chef.name, 'slug': chef.slug, 'email': chef.email, 'is_active': chef.is_active,
                'has_login': chef.user_id is not None}


class TeamChefSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source='city.name')
    cuisine = serializers.CharField(source='get_cuisine_display')
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.IntegerField()
    has_login = serializers.SerializerMethodField()
    national_id = serializers.SerializerMethodField()
    food_handler_certificate = serializers.SerializerMethodField()

    class Meta:
        model = Chef
        fields = [
            'id', 'slug', 'name', 'city', 'area', 'cuisine', 'phone', 'is_active', 'is_accepting_bookings',
            'is_featured', 'is_verified', 'documents_updated_at', 'avg_rating', 'review_count', 'has_login',
            'application_id', 'national_id', 'food_handler_certificate',
        ]

    def get_avg_rating(self, chef):
        return round(chef.avg_rating, 1) if chef.avg_rating is not None else None

    def get_has_login(self, chef):
        return chef.user_id is not None

    def get_national_id(self, chef):
        return file_url(chef.national_id)

    def get_food_handler_certificate(self, chef):
        return file_url(chef.food_handler_certificate)


class TeamReviewSerializer(serializers.ModelSerializer):
    chef = serializers.CharField(source='chef.name')
    status_display = serializers.CharField(source='get_status_display')
    booking = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'customer_name', 'rating', 'comment', 'status', 'status_display', 'created_at', 'chef', 'booking']

    def get_booking(self, review):
        booking = review.booking
        return {'id': booking.pk, 'payment_reference': booking.payment_reference, 'event_date': booking.event_date} if booking else None


class MatchRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display')
    occasion_display = serializers.CharField(source='get_occasion_display')
    guests_display = serializers.CharField(source='get_guests_display')
    cuisine_display = serializers.CharField(source='get_cuisine_display')
    time_slot_display = serializers.CharField(source='get_time_slot_display')

    class Meta:
        model = ChefMatchRequest
        fields = [
            'id', 'full_name', 'phone', 'email', 'status', 'status_display', 'occasion_display', 'guests_display',
            'cuisine_display', 'event_date', 'time_slot_display', 'location', 'notes', 'created_at',
        ]


class ContactMessageSerializer(serializers.ModelSerializer):
    subject_display = serializers.CharField(source='get_subject_display')

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject_display', 'message', 'is_handled', 'created_at']

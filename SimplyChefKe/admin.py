from urllib.parse import quote

from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.html import format_html

from . import notifications
from .accounts import approve_application, invite_chef, reject_application
from .forms import ApproveApplicationForm, RejectApplicationForm
from .models import (
    BookingMessage, BookingRequest, Chef, ChefApplication, ChefMatchRequest, ChefPackage, ChefPhoto, ChefTimeOff, City, ContactMessage,
    DishPhoto, Review, ServiceCategory, Subscriber,
)


def image_preview(image, height=90):
    if image:
        return format_html('<img src="{}" style="height:{}px;border-radius:6px;">', image.url, height)
    return '-'


class DishPhotoInline(admin.TabularInline):
    model = DishPhoto
    extra = 0
    readonly_fields = ['preview']

    @admin.display(description='Preview')
    def preview(self, obj):
        return image_preview(obj.image)


@admin.register(ChefApplication)
class ChefApplicationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'chat', 'location', 'cuisine', 'services', 'years_experience', 'status', 'has_profile', 'created_at']
    list_filter = ['status', 'chef_type', 'services', 'cuisine']
    search_fields = ['full_name', 'phone', 'email', 'location']
    readonly_fields = ['decision_message', 'created_at', 'reviewed_at']
    inlines = [DishPhotoInline]
    actions = ['approve', 'reject']
    fieldsets = [
        ('Personal details', {'fields': ['full_name', 'phone', 'email', 'location']}),
        ('Cooking profile', {'fields': ['chef_type', 'services', 'cuisine', 'years_experience', 'bio']}),
        ('Documents', {'fields': ['national_id', 'food_handler_certificate', 'agreed_to_terms']}),
        ('Review', {'fields': ['status', 'admin_notes', 'decision_message', 'created_at', 'reviewed_at']}),
    ]

    @admin.display(description='Chat')
    def chat(self, obj):
        return whatsapp_link(obj.phone, f'Hi {obj.full_name.split()[0]}, this is Karamu about your chef application.')

    @admin.display(boolean=True, description='Profile')
    def has_profile(self, obj):
        return hasattr(obj, 'chef')

    def decision_page(self, request, queryset, action, form_class, title):
        """Ask for the welcome message / rejection reason before the action runs.

        Returns (page, None) while asking, then (None, cleaned_data) once the form is sent.
        """
        form = form_class(request.POST if 'apply' in request.POST else None)
        if form.is_bound and form.is_valid():
            return None, form.cleaned_data
        return TemplateResponse(request, 'admin/SimplyChefKe/chefapplication/decision.html', {
            **self.admin_site.each_context(request),
            'title': title,
            'opts': self.model._meta,
            'applications': queryset,
            'action': action,
            'form': form,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }), None

    @admin.action(description='Approve: create their profile and email them a welcome + login')
    def approve(self, request, queryset):
        page, data = self.decision_page(request, queryset, 'approve', ApproveApplicationForm, 'Approve and welcome these chefs')
        if page:
            return page
        approved = 0
        for app in queryset.filter(chef__isnull=True):
            try:
                approve_application(app, data['message'])
            except ValueError as e:
                self.message_user(request, f'{app.full_name} approved, but no login sent: {e}', level=messages.WARNING)
            approved += 1
        msg = (f'{approved} application(s) approved and chefs emailed. They add a photo, packages and prices '
               f'themselves; tick "Live on marketplace" under Chefs when the profile is ready.')
        if skipped := queryset.count() - approved:
            msg += f' {skipped} skipped (already has a profile).'
        self.message_user(request, msg)

    @admin.action(description='Reject: email them the reason they were not accepted')
    def reject(self, request, queryset):
        page, data = self.decision_page(request, queryset, 'reject', RejectApplicationForm, 'Reject these applications')
        if page:
            return page
        rejected = 0
        for app in queryset.exclude(status=ChefApplication.Status.REJECTED).filter(chef__isnull=True):
            reject_application(app, data['reason'])
            rejected += 1
        self.message_user(request, f'{rejected} application(s) rejected and applicants emailed.')


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'starting_price', 'price_unit', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ['name']}


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ['name']}


class ChefPackageInline(admin.StackedInline):
    model = ChefPackage
    extra = 1


class ChefPhotoInline(admin.TabularInline):
    model = ChefPhoto
    extra = 1
    readonly_fields = ['preview']

    @admin.display(description='Preview')
    def preview(self, obj):
        return image_preview(obj.image)


class BookingMessageInline(admin.TabularInline):
    model = BookingMessage
    extra = 0
    fields = ['created_at', 'from_chef', 'body']
    readonly_fields = ['created_at', 'from_chef', 'body']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ChefTimeOffInline(admin.TabularInline):
    model = ChefTimeOff
    extra = 0


@admin.register(Chef)
class ChefAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'cuisine', 'starting_price', 'has_login', 'is_active', 'is_accepting_bookings', 'is_verified', 'is_featured']
    list_filter = ['is_active', 'is_accepting_bookings', 'is_verified', 'is_featured', 'city', 'services', 'cuisine']
    list_editable = ['is_active', 'is_featured']
    search_fields = ['name', 'headline', 'area', 'phone', 'email']
    prepopulated_fields = {'slug': ['name']}
    filter_horizontal = ['services']
    raw_id_fields = ['user']
    readonly_fields = ['photo_preview', 'created_at']
    inlines = [ChefPackageInline, ChefPhotoInline, ChefTimeOffInline]
    actions = ['send_login_invites']
    fieldsets = [
        ('Profile', {'fields': ['name', 'slug', 'headline', 'bio', 'photo', 'photo_preview', 'cover_image']}),
        ('Services & location', {'fields': ['services', 'cuisine', 'city', 'area', 'years_experience']}),
        ('Pricing', {'fields': ['starting_price', 'price_unit']}),
        ('Contact (private)', {'fields': ['phone', 'email', 'application', 'user']}),
        ('Documents (private)', {'fields': ['national_id', 'food_handler_certificate', 'documents_updated_at']}),
        ('Visibility', {'fields': ['is_active', 'is_accepting_bookings', 'is_verified', 'is_featured', 'created_at']}),
    ]

    @admin.display(description='Current photo')
    def photo_preview(self, obj):
        return image_preview(obj.photo, 120)

    @admin.display(boolean=True, description='Login')
    def has_login(self, obj):
        return obj.user_id is not None

    @admin.action(description='Email selected chefs a link to set their password')
    def send_login_invites(self, request, queryset):
        sent = 0
        for chef in queryset:
            try:
                invite_chef(chef)
                sent += 1
            except ValueError as e:
                self.message_user(request, f'{chef.name}: {e}', level=messages.WARNING)
        self.message_user(request, f'Login link sent to {sent} chef(s).')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['chef', 'customer_name', 'rating', 'status', 'booking', 'created_at']
    list_filter = ['status', 'rating']
    search_fields = ['customer_name', 'comment', 'chef__name']
    raw_id_fields = ['customer', 'booking']
    actions = ['publish', 'decline']

    @admin.action(description='Publish selected reviews and tell the chef')
    def publish(self, request, queryset):
        reviews = list(queryset.exclude(status=Review.Status.PUBLISHED).select_related('chef'))
        for review in reviews:
            review.status = Review.Status.PUBLISHED
            review.save(update_fields=['status'])
            notifications.review_published(review)
        self.message_user(request, f'{len(reviews)} review(s) published.')

    @admin.action(description='Decline selected reviews (hide them)')
    def decline(self, request, queryset):
        self.message_user(request, f'{queryset.update(status=Review.Status.REJECTED)} review(s) declined.')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'status' in form.changed_data and obj.status == Review.Status.PUBLISHED:
            notifications.review_published(obj)


def whatsapp_link(phone, text=''):
    """Click-to-chat link that opens WhatsApp with this number (+2547XXXXXXXX)."""
    return format_html(
        '<a href="https://wa.me/{}?text={}" target="_blank" rel="noopener">WhatsApp</a>',
        phone.lstrip('+'), quote(text),
    )


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    inlines = [BookingMessageInline]
    list_display = ['full_name', 'phone', 'chat', 'chef', 'package', 'event_date', 'time_slot', 'guests', 'status', 'price', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'time_slot', 'chef']
    list_editable = ['status']
    search_fields = ['full_name', 'phone', 'email', 'chef__name', 'location', 'mpesa_code']
    raw_id_fields = ['customer']
    readonly_fields = ['paid_at', 'reminder_sent_at', 'created_at']
    date_hierarchy = 'event_date'

    @admin.display(description='Chat')
    def chat(self, obj):
        return whatsapp_link(
            obj.phone,
            f'Hi {obj.full_name.split()[0]}, this is Karamu about your booking with {obj.chef.name} '
            f'on {obj.event_date:%d %b}.',
        )

    def save_model(self, request, obj, form, change):
        if 'payment_status' in form.changed_data and obj.payment_status == BookingRequest.PaymentStatus.PAID:
            obj.paid_at = obj.paid_at or timezone.now()
        super().save_model(request, obj, form, change)
        # Also runs for the status dropdowns on the list page
        if change and 'status' in form.changed_data and obj.status in notifications.BOOKING_STATUS_MESSAGES:
            notifications.booking_status_changed(obj, by_team=True)
        if change and 'payment_status' in form.changed_data:
            notifications.payment_status_changed(obj)


@admin.register(ChefMatchRequest)
class ChefMatchRequestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'chat', 'occasion', 'guests', 'cuisine', 'event_date', 'time_slot', 'location', 'status', 'created_at']
    list_filter = ['status', 'occasion', 'cuisine']
    list_editable = ['status']
    search_fields = ['full_name', 'phone', 'email', 'location']
    raw_id_fields = ['matched_booking']
    date_hierarchy = 'event_date'

    @admin.display(description='Chat')
    def chat(self, obj):
        return whatsapp_link(
            obj.phone,
            f'Hi {obj.full_name.split()[0]}, this is Karamu about your {obj.get_occasion_display().lower()} '
            f'on {obj.event_date:%d %b}.',
        )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'subject', 'is_handled', 'created_at']
    list_filter = ['is_handled', 'subject']
    list_editable = ['is_handled']
    search_fields = ['name', 'email', 'phone', 'message']


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['email']

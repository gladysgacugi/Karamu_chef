import datetime
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Prefetch, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import notifications
from .accounts import approve_application, reject_application
from .forms import (
    MAX_CHEF_PHOTOS, AddPhotosForm, ApproveApplicationForm, BookingMessageForm, BookingRequestForm, BookingStatusForm, ChefApplicationForm,
    ChefDocumentsForm, ChefMatchRequestForm, ChefPackageFormSet, ChefPhotoFormSet, ChefProfileForm, ContactForm,
    EmailLoginForm, PaymentForm, RejectApplicationForm, ReviewForm, SignUpForm, SubscribeForm, TeamBookingForm,
    TimeOffForm,
)
from .models import (
    BookingRequest, Chef, ChefApplication, ChefMatchRequest, ChefPackage, ChefPhoto, ChefTimeOff, City, ContactMessage,
    DishPhoto, Review, ServiceCategory,
)


SORT_OPTIONS = {
    'featured': ('Featured', ['-is_featured', F('avg_rating').desc(nulls_last=True)]),
    'rating': ('Top rated', [F('avg_rating').desc(nulls_last=True), '-review_count']),
    'price_low': ('Price: low to high', ['starting_price']),
    'price_high': ('Price: high to low', ['-starting_price']),
}


HOMEPAGE_FORMS = {
    'chef_form': ChefApplicationForm,
    'match_form': ChefMatchRequestForm,
    'contact_form': ContactForm,
    'subscribe_form': SubscribeForm,
}


def index(request, status=200, **forms):
    """The homepage. A form that failed to submit is passed in so it is shown again with its errors."""
    live_chefs = Chef.objects.live()
    offered_packages = ChefPackage.objects.filter(chef__is_active=True, is_active=True)
    packages = (
        offered_packages
        .select_related('chef__city', 'service')
        .order_by('-chef__is_featured', 'order', 'price')[:6]
    )
    return render(request, 'index.html', {
        **{name: forms.get(name) or form_class() for name, form_class in HOMEPAGE_FORMS.items()},
        'services': ServiceCategory.objects.all(),
        'cities': City.objects.all(),
        'featured_chefs': live_chefs.with_ratings().filter(is_featured=True)[:4],
        'packages': packages,
        'package_services': sorted({p.service for p in packages if p.service}, key=lambda s: (s.order, s.name)),
        'reviews': Review.objects.filter(
            status=Review.Status.PUBLISHED, chef__is_active=True, rating__gte=4,
        ).select_related('chef')[:8],
        'stats': {
            'chefs': live_chefs.count(),
            'verified': live_chefs.filter(is_verified=True).count(),
            'packages': offered_packages.count(),
            'cities': City.objects.filter(chefs__is_active=True).distinct().count(),
        },
    }, status=status)


# ---------------------------------------------------------------------------
# Saving the customer forms. Shared with the JSON API (api_forms.py), so both
# sites do the same thing and show the same message.
# ---------------------------------------------------------------------------

def save_chef_application(form):
    with transaction.atomic():
        application = form.save()
        for photo in form.cleaned_data['dish_photos']:
            DishPhoto.objects.create(application=application, image=photo)
    notifications.application_created(application)
    return application


def save_match_request(form):
    notifications.match_request_created(form.save())
    return "Request received! We'll match you with a chef and get back to you by SMS or WhatsApp shortly."


def save_contact_message(form):
    notifications.contact_message_created(form.save())
    return "Message sent! We'll reply as soon as we can."


def save_subscription(form):
    already = form.save()
    return "You're already subscribed - thank you!" if already else "You're subscribed! Look out for new chefs and specials in your inbox."


def save_booking(request, chef, form):
    """A new booking with the chef, made by the logged-in customer if there is one."""
    booking = form.save(commit=False)
    booking.chef = chef
    if request.user.is_authenticated:
        booking.customer = request.user
    booking.save()
    notifications.booking_created(booking)
    remember_booking(request, booking)
    return booking


def submit_payment(booking, mpesa_code):
    booking.mpesa_code = mpesa_code
    booking.payment_status = BookingRequest.PaymentStatus.SUBMITTED
    booking.save(update_fields=['mpesa_code', 'payment_status'])
    notifications.payment_submitted(booking)
    return "Thank you! We're checking your payment and will email you as soon as it's confirmed."


def save_review(booking, form):
    review = form.save(commit=False)
    review.chef, review.booking, review.customer = booking.chef, booking, booking.customer
    review.save()
    notifications.review_created(review)
    return 'Thank you for your review! It will appear on the profile once our team has checked it.'


REVIEW_TOO_EARLY = 'You can review your chef once the booking is completed.'


def customer_cancel(booking):
    """Cancel a booking request for its customer. Returns whether it worked and the message to show."""
    if not booking.customer_can_cancel:
        return False, 'This booking is already confirmed. Please WhatsApp us to change or cancel it.'
    booking.status = BookingRequest.Status.CANCELLED
    booking.save(update_fields=['status'])
    notifications.booking_cancelled_by_customer(booking)
    return True, f'Your booking with {booking.chef.name} was cancelled.'


def become_chef(request):
    """The chef application page. The homepage form posts here too, so errors and the thank-you show on this page."""
    if request.method != 'POST':
        return render(request, 'become_a_chef.html', {'form': ChefApplicationForm(), 'sent': 'sent' in request.GET})

    form = ChefApplicationForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'become_a_chef.html', {'form': form}, status=400)
    save_chef_application(form)
    return redirect(f"{reverse('become_chef')}?sent=1")


@require_POST
def request_chef(request):
    """The homepage 'Book a Private Chef' form, for customers who want us to find them a chef."""
    form = ChefMatchRequestForm(request.POST)
    if not form.is_valid():
        return index(request, status=400, match_form=form)
    messages.success(request, save_match_request(form), extra_tags='match')
    return redirect('/#reservation')


@require_POST
def contact(request):
    form = ContactForm(request.POST)
    if not form.is_valid():
        return index(request, status=400, contact_form=form)
    messages.success(request, save_contact_message(form), extra_tags='contact')
    return redirect('/#contact-section')


@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    if not form.is_valid():
        return index(request, status=400, subscribe_form=form)
    messages.success(request, save_subscription(form), extra_tags='newsletter')
    return redirect('/#newsletter')


def filter_marketplace(params):
    """Live chefs matching the marketplace filters in `params` (service, city, q, sort). Shared with the API."""
    chefs = Chef.objects.live().with_ratings().select_related('city').prefetch_related('services')

    service = ServiceCategory.objects.filter(slug=params.get('service')).first()
    city = City.objects.filter(slug=params.get('city')).first()
    query = params.get('q', '').strip()
    sort = params.get('sort') if params.get('sort') in SORT_OPTIONS else 'featured'

    if service:
        chefs = chefs.filter(services=service)
    if city:
        chefs = chefs.filter(city=city)
    if query:
        chefs = chefs.filter(
            Q(name__icontains=query) | Q(headline__icontains=query) | Q(bio__icontains=query)
            | Q(area__icontains=query) | Q(packages__name__icontains=query, packages__is_active=True)
        ).distinct()
    return chefs.order_by(*SORT_OPTIONS[sort][1]), service, city, query, sort


def marketplace(request):
    chefs, service, city, query, sort = filter_marketplace(request.GET)

    page = Paginator(chefs, 12).get_page(request.GET.get('page'))

    # Keep the active filters when moving between pages
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'marketplace.html', {
        'page': page,
        'services': ServiceCategory.objects.all(),
        'cities': City.objects.all(),
        'active_service': service,
        'active_city': city,
        'query': query,
        'sort': sort,
        'sort_options': {key: label for key, (label, _) in SORT_OPTIONS.items()},
        'filter_params': params.urlencode(),
    })


# Session key listing the bookings made in this browser, so guests can open their confirmation page
GUEST_BOOKINGS_KEY = 'booking_ids'


def booking_initial(user):
    """Pre-fill the booking form for a logged-in customer from their account and last booking."""
    if not user.is_authenticated:
        return {}
    initial = {'full_name': user.get_full_name(), 'email': user.email}
    last = user.bookings.order_by('-created_at').first()
    if last:
        initial.update(phone=last.phone, location=last.location)
    return initial


def chef_detail(request, slug):
    visible = Q(is_active=True)
    if request.user.is_authenticated:
        visible |= Q(user=request.user)  # chefs can preview their own profile before it goes live
    chef = get_object_or_404(
        Chef.objects.filter(visible).with_ratings().select_related('city').prefetch_related(
            'services', 'photos', Prefetch('packages', queryset=ChefPackage.objects.filter(is_active=True)),
        ),
        slug=slug,
    )
    initial = {'package': request.GET.get('package'), **booking_initial(request.user)}
    return render(request, 'chef_detail.html', {
        'chef': chef,
        'is_own_profile': request.user.is_authenticated and chef.user_id == request.user.pk,
        'reviews': chef.reviews.filter(status=Review.Status.PUBLISHED)[:20],
        # A completed booking with this chef that the logged-in customer hasn't reviewed yet
        'booking_to_review': request.user.bookings.filter(
            chef=chef, status=BookingRequest.Status.COMPLETED, review__isnull=True,
        ).first() if request.user.is_authenticated else None,
        'time_off': chef.upcoming_time_off()[:6],
        'booking_form': BookingRequestForm(chef=chef, initial=initial),
        'similar_chefs': Chef.objects.live().with_ratings().filter(city=chef.city).exclude(pk=chef.pk)[:3],
    })


def book_chef(request, slug):
    """The booking page. The form on the chef's profile posts here too."""
    chef = get_object_or_404(Chef.objects.live().with_ratings().select_related('city'), slug=slug)
    context = {'chef': chef, 'packages': chef.packages.filter(is_active=True), 'time_off': chef.upcoming_time_off()[:6]}
    if request.method != 'POST':
        initial = {'package': request.GET.get('package'), **booking_initial(request.user)}
        return render(request, 'booking.html', {**context, 'form': BookingRequestForm(chef=chef, initial=initial)})

    form = BookingRequestForm(request.POST, chef=chef)
    if not form.is_valid():
        return render(request, 'booking.html', {**context, 'form': form}, status=400)
    booking = save_booking(request, chef, form)
    return redirect('booking_confirmation', pk=booking.pk)


def remember_booking(request, booking):
    request.session[GUEST_BOOKINGS_KEY] = [*request.session.get(GUEST_BOOKINGS_KEY, []), booking.pk][-20:]


def customer_booking(request, pk):
    """A booking, for its customer only: logged in as them, booked in this browser, or opened from their email.

    Returns the booking and whether it belongs to the logged-in user.
    """
    booking = get_object_or_404(BookingRequest.objects.select_related('chef', 'package'), pk=pk)
    is_owner = request.user.is_authenticated and booking.customer_id == request.user.pk
    if not is_owner and pk not in request.session.get(GUEST_BOOKINGS_KEY, []):
        if BookingRequest.pk_from_key(request.GET.get('key', '')) != pk:
            raise Http404
        remember_booking(request, booking)  # so links on the page work without the key
    return booking, is_owner


def customer_message_form(booking, data=None):
    return BookingMessageForm(data, placeholder=f'Write to {booking.chef.name}...')


def booking_confirmation(request, pk):
    """A booking's summary, payment, what happens next, and messages with the chef."""
    booking, is_owner = customer_booking(request, pk)
    form = customer_message_form(booking, request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        send_booking_message(booking, form, from_chef=False)
        messages.success(request, f'Message sent to {booking.chef.name}.')
        return redirect(f"{reverse('booking_confirmation', args=[pk])}#messages")
    return render(request, 'booking_confirmation.html', {
        'booking': booking, 'is_owner': is_owner, 'message_form': form, 'booking_messages': booking.messages.all(),
    }, status=400 if form.errors else 200)


def booking_checkout(request, pk):
    """How to pay for a confirmed booking by M-Pesa, and where the customer sends us their M-Pesa code."""
    booking, is_owner = customer_booking(request, pk)
    if not booking.customer_can_pay:
        return redirect('booking_confirmation', pk=pk)

    form = PaymentForm(request.POST or None, booking=booking)
    if request.method == 'POST' and form.is_valid():
        messages.success(request, submit_payment(booking, form.cleaned_data['mpesa_code']))
        return redirect('booking_confirmation', pk=pk)

    return render(request, 'booking_checkout.html', {
        'booking': booking, 'is_owner': is_owner, 'form': form, 'paybill': settings.MPESA_PAYBILL,
    }, status=400 if form.errors else 200)


def booking_review(request, pk):
    """Customers review a chef from their completed booking, so every review is from a real booking."""
    booking, is_owner = customer_booking(request, pk)
    if not booking.can_be_reviewed:
        if booking.status != BookingRequest.Status.COMPLETED:
            messages.error(request, REVIEW_TOO_EARLY)
        return redirect('booking_confirmation', pk=pk)

    form = ReviewForm(request.POST or None, initial={'customer_name': booking.full_name.split()[0]})
    if request.method == 'POST' and form.is_valid():
        messages.success(request, save_review(booking, form))
        return redirect('booking_confirmation', pk=pk)

    return render(request, 'booking_review.html', {
        'booking': booking, 'form': form,
    }, status=400 if form.errors else 200)


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

def home_for(user):
    if user.is_staff:
        return reverse('team_home')
    return reverse('chef_dashboard') if hasattr(user, 'chef_profile') else reverse('account')


def safe_next(request, default):
    """The ?next= page to return to, as long as it is on this site."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, request.is_secure()):
        return next_url
    return default


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return home_for(self.request.user)


def welcome_message(user):
    return f'Welcome to Karamu, {user.first_name}! Your bookings will show up here.'


def signup(request):
    if request.user.is_authenticated:
        return redirect(home_for(request.user))
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, welcome_message(user))
        return redirect(safe_next(request, reverse('account')))
    return render(request, 'accounts/signup.html', {'form': form, 'next': request.GET.get('next', '')})


@login_required
def account(request):
    bookings = request.user.bookings.select_related('chef', 'package', 'review').order_by('-event_date')
    return render(request, 'accounts/account.html', {
        'bookings': bookings,
        'chef': getattr(request.user, 'chef_profile', None),
    })


@login_required
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(BookingRequest, pk=pk, customer=request.user)
    cancelled, message = customer_cancel(booking)
    (messages.success if cancelled else messages.error)(request, message)
    return redirect('account')


def chef_required(view):
    """Only logged-in users with a chef profile. The chef is passed to the view."""
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        chef = Chef.objects.filter(user=request.user).first()
        if chef is None:
            messages.error(request, "That page is for chef partners. Apply to become a chef and we'll set up your account.")
            return redirect('account')
        return view(request, chef, *args, **kwargs)
    return wrapper


def chef_bookings(chef, status):
    """The chef's bookings with how many messages each has, filtered by `status` (anything else means all).

    Returns the bookings and the status tabs. Shared with the API, like the other chef and team functions below.
    """
    bookings = chef.bookings.select_related('package').annotate(message_count=Count('messages'))
    counts = dict(bookings.values_list('status').annotate(n=Count('pk')).order_by())
    if status in BookingRequest.Status.values:
        bookings = bookings.filter(status=status)
    else:
        status = ''
    return bookings.order_by('event_date') if status in ('new', 'confirmed') else bookings, {
        'status': status,
        'status_tabs': [(value, label, counts.get(value, 0)) for value, label in BookingRequest.Status.choices],
        'total': sum(counts.values()),
    }


@chef_required
def chef_dashboard(request, chef):
    bookings, tabs = chef_bookings(chef, request.GET.get('status'))
    return render(request, 'chef/dashboard.html', {'chef': chef, 'bookings': bookings, **tabs})


def send_booking_message(booking, form, from_chef):
    """Save a chef's or customer's message about a booking and email it to the other side."""
    message = form.save(commit=False)
    message.booking, message.from_chef = booking, from_chef
    message.save()
    notifications.booking_message_sent(message)
    return message


def chef_message_form(booking, data=None):
    return BookingMessageForm(data, placeholder=f'Write to {booking.full_name.split()[0]}...')


def chef_message_sent(booking):
    return (f'Message sent to {booking.full_name}.' if booking.email
            else 'Message sent. The customer will see it on their booking page.')


@chef_required
def chef_booking(request, chef, pk):
    """One booking: its details, confirm/decline, and messages with the customer."""
    booking = get_object_or_404(chef.bookings.select_related('package'), pk=pk)
    form = chef_message_form(booking, request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        send_booking_message(booking, form, from_chef=True)
        messages.success(request, chef_message_sent(booking))
        return redirect(f"{reverse('chef_booking', args=[pk])}#messages")
    return render(request, 'chef/booking.html', {
        'chef': chef, 'booking': booking, 'form': form, 'booking_messages': booking.messages.all(),
    }, status=400 if form.errors else 200)


def change_booking_status(booking, data, by_team=False):
    """The chef or the team moving a booking on (BookingStatusForm). Returns whether it worked and the message to show."""
    form = BookingStatusForm(data, booking=booking)
    if not form.is_valid():
        return False, form.first_error()
    form.apply()
    notifications.booking_status_changed(booking, by_team=by_team)
    done = f'Booking for {booking.full_name} marked {booking.get_status_display().lower()}.'
    return True, f'{done} They have been emailed.' if by_team else done


@chef_required
@require_POST
def update_booking_status(request, chef, pk):
    changed, message = change_booking_status(get_object_or_404(BookingRequest, pk=pk, chef=chef), request.POST)
    (messages.success if changed else messages.error)(request, message)
    return redirect(safe_next(request, reverse('chef_dashboard')))


def set_accepting_bookings(chef, accepting):
    chef.is_accepting_bookings = accepting
    chef.save(update_fields=['is_accepting_bookings'])
    return ('You are taking new bookings again.' if accepting
            else 'New bookings are paused. Customers can still see your profile.')


def time_off_form(chef, data=None):
    return TimeOffForm(data, instance=ChefTimeOff(chef=chef))


def save_time_off(chef, form):
    """Returns the message to show, and a warning if the chef has confirmed bookings on those days (or None)."""
    time_off = form.save()
    clashes = chef.bookings.filter(
        status=BookingRequest.Status.CONFIRMED, event_date__range=[time_off.start_date, time_off.end_date],
    ).count()
    warning = (f'You have {clashes} confirmed booking{"s" if clashes > 1 else ""} on those dates. '
               'Please honour them or WhatsApp us so we can help the customer.') if clashes else None
    return 'Time off saved. Customers cannot book you on those dates.', warning


TIME_OFF_REMOVED = 'Time off removed.'


def upcoming_confirmed(chef):
    return chef.bookings.filter(
        status=BookingRequest.Status.CONFIRMED, event_date__gte=datetime.date.today(),
    ).select_related('package').order_by('event_date', 'time_slot')[:20]


@chef_required
def chef_availability(request, chef):
    """Time off and pausing new bookings."""
    form = time_off_form(chef)
    if request.method == 'POST' and 'accepting' in request.POST:
        messages.success(request, set_accepting_bookings(chef, request.POST['accepting'] == '1'))
        return redirect('chef_availability')

    if request.method == 'POST':
        form = time_off_form(chef, request.POST)
        if form.is_valid():
            message, warning = save_time_off(chef, form)
            messages.success(request, message)
            if warning:
                messages.error(request, warning)
            return redirect('chef_availability')

    return render(request, 'chef/availability.html', {
        'chef': chef,
        'form': form,
        'time_off': chef.upcoming_time_off(),
        'upcoming': upcoming_confirmed(chef),
    }, status=400 if form.errors else 200)


@chef_required
@require_POST
def chef_time_off_delete(request, chef, pk):
    get_object_or_404(ChefTimeOff, pk=pk, chef=chef).delete()
    messages.success(request, TIME_OFF_REMOVED)
    return redirect('chef_availability')


FIX_FIELDS = 'Please correct the highlighted fields.'


def chef_profile_forms(chef, data=None, files=None):
    """The profile form and the packages formset."""
    return ChefProfileForm(data, files, instance=chef), ChefPackageFormSet(data, instance=chef, prefix='packages')


def save_chef_profile(chef, form, packages):
    with transaction.atomic():
        form.save()
        packages.save()
    return 'Profile saved.' if chef.is_active else 'Profile saved. Our team will set it live once it is complete.'


@chef_required
def chef_profile_edit(request, chef):
    """Profile, packages and prices."""
    form, packages = chef_profile_forms(chef, *((request.POST, request.FILES) if request.method == 'POST' else ()))

    if request.method == 'POST':
        if form.is_valid() and packages.is_valid():
            messages.success(request, save_chef_profile(chef, form, packages))
            return redirect('chef_profile_edit')
        messages.error(request, FIX_FIELDS)

    return render(request, 'chef/profile_edit.html', {
        'chef': chef, 'form': form, 'packages': packages,
    }, status=400 if request.method == 'POST' else 200)


def chef_photo_forms(chef, data=None, files=None):
    """The gallery formset (captions, remove) and the form to add photos, with room for the ones being removed."""
    photos = ChefPhotoFormSet(data, instance=chef, prefix='photos')
    removing = sum(1 for f in photos.forms if f.data.get(f'{f.prefix}-DELETE')) if data else 0
    return photos, AddPhotosForm(data, files, room=MAX_CHEF_PHOTOS - chef.photos.count() + removing)


def save_chef_photos(chef, photos, add):
    new = add.cleaned_data['new_photos']
    with transaction.atomic():
        photos.save()
        for image in new:
            ChefPhoto.objects.create(chef=chef, image=image)
    return f'{len(new)} photo{"s" if len(new) != 1 else ""} added.' if new else 'Photos saved.'


@chef_required
def chef_photos(request, chef):
    """The food photo gallery: add several at once, change captions, remove."""
    photos, add = chef_photo_forms(chef, *((request.POST, request.FILES) if request.method == 'POST' else ()))

    if request.method == 'POST':
        if photos.is_valid() and add.is_valid():
            messages.success(request, save_chef_photos(chef, photos, add))
            return redirect('chef_photos')
        messages.error(request, FIX_FIELDS)

    return render(request, 'chef/photos.html', {
        'chef': chef, 'photos': photos, 'add': add, 'max_photos': MAX_CHEF_PHOTOS,
    }, status=400 if request.method == 'POST' else 200)


def save_chef_documents(form):
    """A new ID or certificate: the badge comes off until the team has checked it."""
    chef = form.save(commit=False)
    chef.documents_updated_at = timezone.now()
    chef.is_verified = False
    chef.save()
    notifications.chef_documents_updated(chef)
    return 'Documents uploaded. Our team will check them and put your "verified" badge back.'


@chef_required
def chef_documents(request, chef):
    """The chef's ID and food handler's certificate. A new upload goes back to the team to check."""
    data, files = (request.POST, request.FILES) if request.method == 'POST' else (None, None)
    form = ChefDocumentsForm(data, files, instance=chef)
    if request.method == 'POST' and form.is_valid():
        messages.success(request, save_chef_documents(form))
        return redirect('chef_documents')
    return render(request, 'chef/documents.html', {
        'chef': chef, 'form': form,
    }, status=400 if form.errors else 200)


# ---------------------------------------------------------------------------
# Team: a phone-friendly admin for the day-to-day work. Staff only.
# ---------------------------------------------------------------------------

def team_waiting():
    """The counts of what is waiting for the team, for the badges on the bottom menu."""
    return {
        'applications': ChefApplication.objects.filter(status=ChefApplication.Status.PENDING).count(),
        'bookings': BookingRequest.objects.filter(status=BookingRequest.Status.NEW).count(),
        'payments': BookingRequest.objects.filter(payment_status=BookingRequest.PaymentStatus.SUBMITTED).count(),
        'reviews': Review.objects.filter(status=Review.Status.PENDING).count(),
        'requests': ChefMatchRequest.objects.filter(status=ChefMatchRequest.Status.NEW).count(),
        'inbox': ContactMessage.objects.filter(is_handled=False).count(),
    }


def team_render(request, template, context):
    return render(request, template, {'waiting': team_waiting(), **context})


def status_tabs(params, queryset, choices, default):
    """Filter by ?status= in `params` (missing means `default`, empty means all). Returns the queryset, status and tabs."""
    counts = dict(queryset.values_list('status').annotate(n=Count('pk')).order_by())
    status = params.get('status', default)
    if status in dict(choices):
        queryset = queryset.filter(status=status)
    else:
        status = ''
    return queryset, status, {
        'status': status,
        'status_tabs': [(value, label, counts.get(value, 0)) for value, label in choices],
        'total': sum(counts.values()),
    }


def team_upcoming():
    """Confirmed bookings in the next 7 days."""
    today = datetime.date.today()
    return BookingRequest.objects.filter(
        status=BookingRequest.Status.CONFIRMED, event_date__range=[today, today + datetime.timedelta(days=7)],
    ).select_related('chef').order_by('event_date', 'time_slot')


@staff_member_required
def team_home(request):
    return team_render(request, 'team/home.html', {
        'upcoming': team_upcoming(),
        'chefs_waiting_to_go_live': Chef.objects.filter(is_active=False).count(),
    })


def team_application_list(params):
    return status_tabs(params, ChefApplication.objects.all(), ChefApplication.Status.choices, ChefApplication.Status.PENDING)


@staff_member_required
def team_applications(request):
    applications, status, tabs = team_application_list(request.GET)
    return team_render(request, 'team/applications.html', {'applications': applications, **tabs})


@staff_member_required
def team_application(request, pk):
    application = get_object_or_404(ChefApplication.objects.prefetch_related('dish_photos'), pk=pk)
    return team_render(request, 'team/application.html', {
        'application': application,
        'chef': getattr(application, 'chef', None),
        'approve_form': ApproveApplicationForm(),
        'reject_form': RejectApplicationForm(),
    })


def team_approve(application, data):
    """Approve an application: a hidden chef profile and a welcome email with their login. Returns (worked, message)."""
    if hasattr(application, 'chef'):
        return False, f'{application.full_name} is already approved and has a chef profile.'
    form = ApproveApplicationForm(data)
    form.is_valid()  # the welcome message is optional, so this always passes
    try:
        approve_application(application, form.cleaned_data['message'])
    except ValueError as e:
        return False, f'{application.full_name} approved, but no login was sent: {e}'
    return True, f'{application.full_name} approved and emailed a welcome with their login.'


def team_reject(application, data):
    """Reject an application and email the reason. Returns (worked, message)."""
    if hasattr(application, 'chef'):
        return False, f'{application.full_name} already has a chef profile. Hide it instead.'
    form = RejectApplicationForm(data)
    if not form.is_valid():
        return False, 'Write the reason for rejection - it goes in the email to the applicant.'
    reject_application(application, form.cleaned_data['reason'])
    return True, f'{application.full_name} rejected and emailed.'


@staff_member_required
@require_POST
def team_approve_application(request, pk):
    approved, message = team_approve(get_object_or_404(ChefApplication, pk=pk), request.POST)
    (messages.success if approved else messages.error)(request, message)
    return redirect('team_application', pk=pk)


@staff_member_required
@require_POST
def team_reject_application(request, pk):
    rejected, message = team_reject(get_object_or_404(ChefApplication, pk=pk), request.POST)
    (messages.success if rejected else messages.error)(request, message)
    return redirect('team_application', pk=pk)


# The team's on/off switches for a chef: the field and what the chef now is, on and off
CHEF_SWITCHES = {
    'live': ('is_active', 'now live on the marketplace', 'hidden from the marketplace'),
    'featured': ('is_featured', 'now shown on the homepage', 'no longer shown on the homepage'),
    'verified': ('is_verified', 'now marked verified', 'no longer marked verified'),
}


def switch_chef(chef, switch, on):
    field, on_text, off_text = CHEF_SWITCHES[switch]
    setattr(chef, field, on)
    chef.save(update_fields=[field])
    return f'{chef.name} is {on_text if on else off_text}.'


@staff_member_required
@require_POST
def team_chef_live(request, pk):
    messages.success(request, switch_chef(get_object_or_404(Chef, pk=pk), 'live', request.POST.get('live') == '1'))
    return redirect(safe_next(request, reverse('team_home')))


@staff_member_required
@require_POST
def team_chef_featured(request, pk):
    messages.success(request, switch_chef(get_object_or_404(Chef, pk=pk), 'featured', request.POST.get('featured') == '1'))
    return redirect(safe_next(request, reverse('team_chefs')))


@staff_member_required
@require_POST
def team_chef_verified(request, pk):
    messages.success(request, switch_chef(get_object_or_404(Chef, pk=pk), 'verified', request.POST.get('verified') == '1'))
    return redirect(safe_next(request, reverse('team_chefs')))


TEAM_CHEF_FILTERS = {
    '': ('All', Q()),
    'live': ('Live', Q(is_active=True)),
    'hidden': ('Not live', Q(is_active=False)),
    'paused': ('Paused bookings', Q(is_active=True, is_accepting_bookings=False)),
    'documents': ('Documents to check', Q(documents_updated_at__isnull=False, is_verified=False)),
}


def team_chef_list(show):
    """Chefs for the ?show= filter (anything else means all). Returns the chefs, the filter and the filter tabs."""
    show = show if show in TEAM_CHEF_FILTERS else ''
    chefs = Chef.objects.with_ratings().select_related('city').order_by('-is_active', 'name')
    return chefs.filter(TEAM_CHEF_FILTERS[show][1]), show, [
        (key, label, Chef.objects.filter(q).count()) for key, (label, q) in TEAM_CHEF_FILTERS.items()
    ]


@staff_member_required
def team_chefs(request):
    chefs, show, filters = team_chef_list(request.GET.get('show'))
    return team_render(request, 'team/chefs.html', {'chefs': chefs, 'show': show, 'filters': filters})


def team_booking_list(params):
    """Bookings by ?status=, or only the payments to check with ?payment=submitted. Returns them, whether only
    payments are shown, and the status tabs."""
    bookings, status, tabs = status_tabs(
        params, BookingRequest.objects.select_related('chef', 'package'),
        BookingRequest.Status.choices, BookingRequest.Status.NEW,
    )
    checking_payments = params.get('payment') == BookingRequest.PaymentStatus.SUBMITTED
    if checking_payments:
        bookings = bookings.filter(payment_status=BookingRequest.PaymentStatus.SUBMITTED)
    if status in ('new', 'confirmed'):
        bookings = bookings.order_by('event_date')
    return bookings, checking_payments, tabs


@staff_member_required
def team_bookings(request):
    bookings, checking_payments, tabs = team_booking_list(request.GET)
    return team_render(request, 'team/bookings.html', {
        'bookings': bookings, 'checking_payments': checking_payments, **tabs,
    })


def booking_clash(booking):
    """A new booking at a time the chef already has a confirmed one."""
    return (booking.status == BookingRequest.Status.NEW
            and booking.chef.slot_taken(booking.event_date, booking.time_slot, exclude=booking))


TEAM_BOOKING_SAVED = 'Booking saved.'


@staff_member_required
def team_booking(request, pk):
    booking = get_object_or_404(BookingRequest.objects.select_related('chef', 'package', 'customer'), pk=pk)
    form = TeamBookingForm(request.POST or None, instance=booking)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, TEAM_BOOKING_SAVED)
        return redirect('team_booking', pk=pk)
    return team_render(request, 'team/booking.html', {
        'booking': booking,
        'form': form,
        'review': getattr(booking, 'review', None),
        'booking_messages': booking.messages.all(),
        'clash': booking_clash(booking),
    })


@staff_member_required
@require_POST
def team_booking_status(request, pk):
    booking = get_object_or_404(BookingRequest.objects.select_related('chef'), pk=pk)
    changed, message = change_booking_status(booking, request.POST, by_team=True)
    (messages.success if changed else messages.error)(request, message)
    return redirect(safe_next(request, reverse('team_bookings')))


PAYMENT_DONE_MESSAGES = {
    'paid': 'Payment from {name} marked paid. The customer and chef have been emailed.',
    'unpaid': "Payment from {name} marked not found. They've been asked to check their M-Pesa code.",
    'refunded': 'Booking for {name} marked refunded. The customer has been emailed.',
}


def set_payment_status(booking, payment_status):
    """The team checked the M-Pesa statement: paid, not found, or refunded after a cancellation. Returns (worked, message)."""
    if payment_status not in booking.team_payment_actions:
        return False, f'This booking is {booking.get_payment_status_display().lower()} and cannot be changed to that.'
    booking.payment_status = payment_status
    if payment_status == BookingRequest.PaymentStatus.PAID:
        booking.paid_at = timezone.now()
    elif payment_status == BookingRequest.PaymentStatus.UNPAID:
        booking.mpesa_code = ''  # so they can enter the right one
    booking.save(update_fields=['payment_status', 'paid_at', 'mpesa_code'])
    notifications.payment_status_changed(booking)
    return True, PAYMENT_DONE_MESSAGES[payment_status].format(name=booking.full_name)


@staff_member_required
@require_POST
def team_booking_payment(request, pk):
    booking = get_object_or_404(BookingRequest.objects.select_related('chef'), pk=pk)
    changed, message = set_payment_status(booking, request.POST.get('payment_status'))
    (messages.success if changed else messages.error)(request, message)
    return redirect(safe_next(request, reverse('team_booking', args=[pk])))


def team_review_list(params):
    return status_tabs(params, Review.objects.select_related('chef', 'booking'), Review.Status.choices, Review.Status.PENDING)


@staff_member_required
def team_reviews(request):
    reviews, status, tabs = team_review_list(request.GET)
    return team_render(request, 'team/reviews.html', {'reviews': reviews, **tabs})


def set_review_status(review, new_status):
    """Publish or decline a review. Returns the message to show, or None if nothing changed."""
    if new_status not in (Review.Status.PUBLISHED, Review.Status.REJECTED) or new_status == review.status:
        return None
    review.status = new_status
    review.save(update_fields=['status'])
    if new_status == Review.Status.PUBLISHED:
        notifications.review_published(review)
        return f'Review by {review.customer_name} published. {review.chef.name} has been emailed.'
    return f'Review by {review.customer_name} declined. It stays hidden.'


@staff_member_required
@require_POST
def team_review_status(request, pk):
    message = set_review_status(get_object_or_404(Review.objects.select_related('chef'), pk=pk), request.POST.get('status'))
    if message:
        messages.success(request, message)
    return redirect(safe_next(request, reverse('team_reviews')))


def team_request_list(params):
    return status_tabs(params, ChefMatchRequest.objects.all(), ChefMatchRequest.Status.choices, ChefMatchRequest.Status.NEW)


@staff_member_required
def team_requests(request):
    match_requests, status, tabs = team_request_list(request.GET)
    return team_render(request, 'team/requests.html', {'match_requests': match_requests, **tabs})


def set_request_status(match, status):
    """Returns the message to show, or None for a status that doesn't exist."""
    if status not in ChefMatchRequest.Status.values:
        return None
    match.status = status
    match.save(update_fields=['status'])
    return f'Request from {match.full_name} marked {match.get_status_display().lower()}.'


@staff_member_required
@require_POST
def team_request_status(request, pk):
    message = set_request_status(get_object_or_404(ChefMatchRequest, pk=pk), request.POST.get('status'))
    if message:
        messages.success(request, message)
    return redirect(safe_next(request, reverse('team_requests')))


def team_inbox_list(show):
    """The contact messages still to reply to, or all of them with ?show=all. Returns them and whether all are shown."""
    show_all = show == 'all'
    return (ContactMessage.objects.all() if show_all else ContactMessage.objects.filter(is_handled=False)), show_all


@staff_member_required
def team_inbox(request):
    inbox, show_all = team_inbox_list(request.GET.get('show'))
    return team_render(request, 'team/inbox.html', {'inbox': inbox, 'show_all': show_all})


def mark_replied(msg):
    msg.is_handled = True
    msg.save(update_fields=['is_handled'])
    return f'Message from {msg.name} marked as replied.'


@staff_member_required
@require_POST
def team_message_replied(request, pk):
    messages.success(request, mark_replied(get_object_or_404(ContactMessage, pk=pk)))
    return redirect(safe_next(request, reverse('team_inbox')))


# The site used to be installable as an app. Phones that installed it still check /sw.js for updates, and this
# version removes the old service worker and its cache, so they just load the website.
REMOVE_SERVICE_WORKER = """\
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.map((key) => caches.delete(key))))
      .then(() => self.registration.unregister())
      .then(() => self.clients.matchAll({type: 'window'}))
      .then((clients) => clients.forEach((client) => client.navigate(client.url)))
  );
});
"""


def service_worker(request):
    return HttpResponse(REMOVE_SERVICE_WORKER, content_type='application/javascript', headers={'Cache-Control': 'no-cache'})

import datetime

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm

from .models import (
    BookingMessage, BookingRequest, Chef, ChefApplication, ChefMatchRequest, ChefPackage, ChefPhoto, ChefTimeOff, ContactMessage, Review,
    Subscriber, MAX_UPLOAD_MB, mpesa_code_validator, validate_file_size,
)

User = get_user_model()


def normalize_phone(phone):
    """Store numbers in one format: +2547XXXXXXXX"""
    phone = phone.replace(' ', '')
    if phone.startswith('0'):
        return '+254' + phone[1:]
    if phone.startswith('254'):
        return '+' + phone
    return phone


class StyledFormMixin:
    """Gives every widget the theme's .fctrl class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.widget.attrs['class'] = 'fctrl'


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Accepts several images from one <input type="file" multiple>."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleImageInput(attrs={'accept': 'image/*'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return [single_clean(data, initial)] if data else []


class ChefApplicationForm(StyledFormMixin, forms.ModelForm):
    MIN_PHOTOS, MAX_PHOTOS = 3, 5

    dish_photos = MultipleImageField(
        label='Photos of your dishes (3 - 5)', validators=[validate_file_size],
        help_text=f'JPG or PNG, up to {MAX_UPLOAD_MB} MB each.',
    )

    # Keep the photos with the other uploads and the terms checkbox last
    field_order = [
        'full_name', 'phone', 'email', 'location',
        'chef_type', 'services', 'cuisine', 'years_experience', 'bio',
        'national_id', 'food_handler_certificate', 'dish_photos', 'agreed_to_terms',
    ]

    class Meta:
        model = ChefApplication
        fields = [
            'full_name', 'phone', 'email', 'location',
            'chef_type', 'services', 'cuisine', 'years_experience', 'bio',
            'national_id', 'food_handler_certificate', 'agreed_to_terms',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Jane Wanjiku'}),
            'phone': forms.TextInput(attrs={'placeholder': '07XX XXX XXX', 'type': 'tel'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@email.com'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Kilimani, Nairobi'}),
            'years_experience': forms.NumberInput(attrs={'min': 0, 'max': 60}),
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell customers about your cooking...'}),
        }
        labels = {
            'agreed_to_terms': 'I confirm these details are true and agree to the Karamu chef terms.',
        }
        help_texts = {
            'national_id': f'PDF, JPG or PNG, up to {MAX_UPLOAD_MB} MB.',
            'food_handler_certificate': f'PDF, JPG or PNG, up to {MAX_UPLOAD_MB} MB.',
        }

    def clean_phone(self):
        return normalize_phone(self.cleaned_data['phone'])

    def clean_agreed_to_terms(self):
        agreed = self.cleaned_data.get('agreed_to_terms')
        if not agreed:
            raise forms.ValidationError('You must agree to the chef terms to apply.')
        return agreed

    def clean_dish_photos(self):
        photos = self.cleaned_data.get('dish_photos') or []
        if not self.MIN_PHOTOS <= len(photos) <= self.MAX_PHOTOS:
            raise forms.ValidationError(f'Please upload between {self.MIN_PHOTOS} and {self.MAX_PHOTOS} photos.')
        return photos


class BookingRequestForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = ['package', 'full_name', 'phone', 'email', 'event_date', 'time_slot', 'guests', 'location', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Jane Wanjiku'}),
            'phone': forms.TextInput(attrs={'placeholder': '07XX XXX XXX', 'type': 'tel'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@email.com'}),
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'guests': forms.NumberInput(attrs={'min': 1}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Kilimani, Nairobi'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Allergies, dietary needs, dishes you would love...'}),
        }

    def __init__(self, *args, chef, **kwargs):
        super().__init__(*args, **kwargs)
        self.chef = chef
        # Only the packages this chef currently offers can be picked
        self.fields['package'].queryset = chef.packages.filter(is_active=True)
        self.fields['package'].empty_label = 'Not sure yet / custom request'
        self.fields['package'].required = False
        self.fields['event_date'].widget.attrs['min'] = datetime.date.today().isoformat()

    def clean_phone(self):
        return normalize_phone(self.cleaned_data['phone'])

    def clean_event_date(self):
        date = self.cleaned_data['event_date']
        if date < datetime.date.today():
            raise forms.ValidationError('Please choose a date from today onwards.')
        if self.chef.is_away(date):
            raise forms.ValidationError(f'{self.chef.name} is away on {date:%a %d %b}. Please choose another date.')
        return date

    def clean(self):
        cleaned = super().clean()
        if not self.chef.is_accepting_bookings:
            raise forms.ValidationError(f'{self.chef.name} is not taking new bookings right now.')
        date, slot = cleaned.get('event_date'), cleaned.get('time_slot')
        if date and slot and self.chef.slot_taken(date, slot):
            self.add_error('time_slot', f'{self.chef.name} is already booked for this time. Please choose another time or date.')
        return cleaned


class ChefMatchRequestForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ChefMatchRequest
        fields = ['full_name', 'phone', 'email', 'occasion', 'guests', 'cuisine', 'event_date', 'time_slot', 'location', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Jane Wanjiku'}),
            'phone': forms.TextInput(attrs={'placeholder': '07XX XXX XXX', 'type': 'tel'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@email.com'}),
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Kilimani, Nairobi'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': "Allergies, dietary needs, budget, dishes you'd love..."}),
        }
        labels = {'full_name': 'Full name', 'email': 'Email address'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cuisine'].choices = [('', 'Let the chef decide')] + ChefApplication.Cuisine.choices
        self.fields['event_date'].widget.attrs['min'] = datetime.date.today().isoformat()

    def clean_phone(self):
        return normalize_phone(self.cleaned_data['phone'])

    def clean_event_date(self):
        date = self.cleaned_data['event_date']
        if date < datetime.date.today():
            raise forms.ValidationError('Please choose a date from today onwards.')
        return date


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Jane Wanjiku'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@email.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '07XX XXX XXX', 'type': 'tel'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your message here...'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        return normalize_phone(phone) if phone else phone


class SubscribeForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'nlinput', 'placeholder': 'Enter your email address...'}))

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

    def save(self):
        """Subscribe, or re-subscribe someone who left. Returns True if they were already on the list."""
        subscriber, created = Subscriber.objects.get_or_create(email=self.cleaned_data['email'])
        already = not created and subscriber.is_active
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=['is_active'])
        return already


class ReviewForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ['customer_name', 'rating', 'comment']
        widgets = {
            'customer_name': forms.TextInput(attrs={'placeholder': 'Your name'}),
            'rating': forms.Select(choices=[(n, f'{n} star{"s" if n > 1 else ""}') for n in range(5, 0, -1)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'How was the food and service?'}),
        }
        labels = {'customer_name': 'Your name', 'comment': 'Your review'}


# ---------------------------------------------------------------------------
# Accounts
# Customers and chefs log in with their email address, which is also stored
# as the Django username.
# ---------------------------------------------------------------------------

class SignUpForm(StyledFormMixin, forms.ModelForm):
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Jane Wanjiku'}))
    password1 = forms.CharField(
        label='Password', strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='At least 8 characters, not just numbers.',
    )
    password2 = forms.CharField(
        label='Confirm password', strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    field_order = ['full_name', 'email', 'password1', 'password2']

    class Meta:
        model = User
        fields = ['email']
        widgets = {'email': forms.EmailInput(attrs={'placeholder': 'you@email.com'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists. Try logging in instead.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "The two passwords don't match.")
        elif p2:
            first, _, last = cleaned.get('full_name', '').partition(' ')
            user = User(username=cleaned.get('email', ''), email=cleaned.get('email', ''), first_name=first, last_name=last)
            try:
                password_validation.validate_password(p2, user)
            except forms.ValidationError as e:
                self.add_error('password1', e)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.first_name, _, user.last_name = self.cleaned_data['full_name'].strip().partition(' ')
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class EmailLoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget.attrs.update({'placeholder': 'you@email.com', 'autocomplete': 'email'})

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class StyledPasswordResetForm(StyledFormMixin, PasswordResetForm):
    def save(self, **kwargs):
        # Our own email, whether the reset was asked for on the Django page or through the API
        kwargs['email_template_name'] = 'accounts/password_reset_email.txt'
        kwargs['subject_template_name'] = 'accounts/password_reset_subject.txt'
        return super().save(**kwargs)


class StyledSetPasswordForm(StyledFormMixin, SetPasswordForm):
    pass


class ChefProfileForm(StyledFormMixin, forms.ModelForm):
    """What a chef can change on their own profile. Name, verification and visibility stay with the team."""

    class Meta:
        model = Chef
        fields = [
            'headline', 'bio', 'photo', 'cover_image', 'services', 'cuisine', 'city', 'area',
            'years_experience', 'starting_price', 'price_unit', 'phone',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5}),
            'services': forms.CheckboxSelectMultiple,
            'photo': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'cover_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'phone': forms.TextInput(attrs={'type': 'tel'}),
            'years_experience': forms.NumberInput(attrs={'min': 0, 'max': 60}),
        }
        labels = {'phone': 'Phone (M-Pesa, private)'}

    def clean_phone(self):
        return normalize_phone(self.cleaned_data['phone'])


class ChefPackageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ChefPackage
        fields = ['name', 'service', 'description', 'price', 'price_unit', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}
        labels = {'is_active': 'Offered to customers'}


class TimeOffForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ChefTimeOff
        fields = ['start_date', 'end_date', 'note']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.TextInput(attrs={'placeholder': 'e.g. Family wedding (only you see this)'}),
        }
        labels = {'start_date': 'First day away', 'end_date': 'Last day away', 'note': 'Note (optional)'}
        help_texts = {'end_date': 'Leave empty for a single day.', 'note': ''}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['end_date'].required = False
        today = datetime.date.today().isoformat()
        self.fields['start_date'].widget.attrs['min'] = today
        self.fields['end_date'].widget.attrs['min'] = today

    def clean_start_date(self):
        date = self.cleaned_data['start_date']
        if date < datetime.date.today():
            raise forms.ValidationError('Please choose a date from today onwards.')
        return date

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('start_date') and not cleaned.get('end_date'):
            cleaned['end_date'] = cleaned['start_date']
        return cleaned


MAX_CHEF_PHOTOS = 12


class ChefPhotoForm(StyledFormMixin, forms.ModelForm):
    """A photo already in the gallery: change its caption or remove it. New ones come in through AddPhotosForm."""

    class Meta:
        model = ChefPhoto
        fields = ['caption']
        widgets = {'caption': forms.TextInput(attrs={'placeholder': 'Caption (optional), e.g. Swahili biryani'})}


class AddPhotosForm(forms.Form):
    """Several food photos at once, as long as the gallery stays within MAX_CHEF_PHOTOS."""

    new_photos = MultipleImageField(
        label='Add photos', required=False, validators=[validate_file_size],
        help_text=f'JPG or PNG, up to {MAX_UPLOAD_MB} MB each.',
    )

    def __init__(self, *args, room, **kwargs):
        super().__init__(*args, **kwargs)
        self.room = room  # how many more photos fit
        self.fields['new_photos'].widget.attrs['class'] = 'fctrl'

    def clean_new_photos(self):
        photos = self.cleaned_data['new_photos']
        if len(photos) > self.room:
            raise forms.ValidationError(
                f'You can have up to {MAX_CHEF_PHOTOS} photos. Remove some first, or add {self.room} or fewer.'
                if self.room else f'You already have {MAX_CHEF_PHOTOS} photos. Remove some to add new ones.'
            )
        return photos


class ChefDocumentsForm(StyledFormMixin, forms.ModelForm):
    """A chef replacing their ID or food handler's certificate. Leaving a field empty keeps the current file."""

    class Meta:
        model = Chef
        fields = ['national_id', 'food_handler_certificate']
        widgets = {
            'national_id': forms.FileInput(attrs={'accept': '.pdf,image/*'}),
            'food_handler_certificate': forms.FileInput(attrs={'accept': '.pdf,image/*'}),
        }

    def clean(self):
        cleaned = super().clean()
        if not self.files:
            raise forms.ValidationError('Choose a new file to upload.')
        return cleaned


class BookingMessageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = BookingMessage
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'maxlength': 2000})}
        labels = {'body': 'Your message'}

    def __init__(self, *args, placeholder='Write a message...', **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].widget.attrs['placeholder'] = placeholder


ChefPackageFormSet = forms.inlineformset_factory(Chef, ChefPackage, form=ChefPackageForm, extra=1, can_delete=True)
ChefPhotoFormSet = forms.inlineformset_factory(Chef, ChefPhoto, form=ChefPhotoForm, extra=0, can_delete=True)


WELCOME_MESSAGE = (
    "Welcome to the Karamu family! We loved your application and can't wait to see what you cook "
    "for our customers. We're excited to work with you - if you need any help setting up your profile, "
    "just WhatsApp us."
)


class ApproveApplicationForm(StyledFormMixin, forms.Form):
    message = forms.CharField(
        label='Welcome message to the chef', required=False, initial=WELCOME_MESSAGE,
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Goes in their welcome email, above the login link.',
    )


class RejectApplicationForm(StyledFormMixin, forms.Form):
    reason = forms.CharField(
        label='Reason for rejection',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. We need a valid food handler\'s certificate. Please apply again once you have one.'}),
        help_text='Emailed to the applicant.',
    )


class BookingStatusForm(forms.Form):
    """A chef (or the team) moving a booking to its next status. Confirming sets the price the customer pays."""

    status = forms.ChoiceField(choices=BookingRequest.Status.choices)
    price = forms.IntegerField(min_value=1, required=False)

    def __init__(self, *args, booking, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking

    def clean_status(self):
        status = self.cleaned_data['status']
        if status not in self.booking.chef_next_statuses:
            raise forms.ValidationError(f'A {self.booking.get_status_display().lower()} booking cannot be changed to that.')
        return status

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == BookingRequest.Status.CONFIRMED:
            booking = self.booking
            if not (cleaned.get('price') or booking.price):
                self.add_error('price', 'Enter the price the customer will pay before confirming.')
            if booking.chef.slot_taken(booking.event_date, booking.time_slot, exclude=booking):
                self.add_error('status', f'{booking.chef.name} already has a confirmed booking at that time.')
        return cleaned

    def first_error(self):
        return next(iter(self.errors.values()))[0]

    def apply(self):
        """Update the booking with the new status (and price)."""
        self.booking.status = self.cleaned_data['status']
        if self.cleaned_data.get('price'):
            self.booking.price = self.cleaned_data['price']
        self.booking.save(update_fields=['status', 'price'])


class PaymentForm(StyledFormMixin, forms.Form):
    mpesa_code = forms.CharField(
        label='M-Pesa code', max_length=12,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. SJK4H7L2QP', 'autocapitalize': 'characters', 'autocomplete': 'off'}),
        help_text='The code at the start of the M-Pesa confirmation SMS.',
    )

    def __init__(self, *args, booking, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking

    def clean_mpesa_code(self):
        code = self.cleaned_data['mpesa_code'].strip().replace(' ', '').upper()
        mpesa_code_validator(code)
        if BookingRequest.objects.filter(mpesa_code=code).exclude(pk=self.booking.pk).exists():
            raise forms.ValidationError('This M-Pesa code has already been used for another booking.')
        return code


class TeamBookingForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = ['price', 'team_notes']
        widgets = {'team_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. Customer asked to move to 7 PM'})}

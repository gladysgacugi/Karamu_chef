import datetime
import io
import shutil
import tempfile

from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .accounts import create_chef_profile, invite_chef, set_password_path
from .models import (
    BookingRequest, Chef, ChefApplication, ChefMatchRequest, ChefPackage, ChefTimeOff, City, ContactMessage, Review,
    ServiceCategory, Subscriber,
)

User = get_user_model()


def make_chef(name='Chef Wanjiru', email='wanjiru@example.com', **kwargs):
    return Chef.objects.create(
        name=name, headline='Kenyan classics', bio='Bio', cuisine='kenyan', city=City.objects.first(),
        starting_price=4500, phone='+254712345678', email=email, **kwargs,
    )


def make_booking(chef, **kwargs):
    return BookingRequest.objects.create(**{
        'chef': chef, 'full_name': 'Grace Muthoni', 'phone': '+254700000000', 'email': 'grace@example.com',
        'event_date': datetime.date.today() + datetime.timedelta(days=7), 'time_slot': 'dinner',
        'guests': 6, 'location': 'Kilimani', **kwargs,
    })


class CustomerAccountTests(TestCase):
    def test_signup_logs_in_and_uses_email_as_username(self):
        resp = self.client.post(reverse('signup'), {
            'full_name': 'Grace Muthoni', 'email': 'Grace@Example.com',
            'password1': 'sukuma-wiki-42', 'password2': 'sukuma-wiki-42',
        })
        self.assertRedirects(resp, reverse('account'))
        user = User.objects.get()
        self.assertEqual((user.username, user.first_name, user.last_name), ('grace@example.com', 'Grace', 'Muthoni'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_signup_rejects_existing_email(self):
        User.objects.create_user('grace@example.com', 'grace@example.com', 'x')
        resp = self.client.post(reverse('signup'), {
            'full_name': 'Grace', 'email': 'GRACE@example.com', 'password1': 'sukuma-wiki-42', 'password2': 'sukuma-wiki-42',
        })
        self.assertContains(resp, 'already exists')

    def test_login_with_any_email_case(self):
        User.objects.create_user('grace@example.com', 'grace@example.com', 'sukuma-wiki-42')
        resp = self.client.post(reverse('login'), {'username': 'Grace@Example.com ', 'password': 'sukuma-wiki-42'})
        self.assertRedirects(resp, reverse('account'))

    def test_booking_while_logged_in_is_linked_and_listed(self):
        user = User.objects.create_user('grace@example.com', 'grace@example.com', 'pw', first_name='Grace')
        chef = make_chef()
        self.client.force_login(user)
        self.client.post(reverse('book_chef', args=[chef.slug]), {
            'full_name': 'Grace M', 'phone': '0712345678', 'event_date': datetime.date.today() + datetime.timedelta(days=3),
            'time_slot': 'lunch', 'guests': 4, 'location': 'Kileleshwa',
        })
        booking = BookingRequest.objects.get()
        self.assertEqual(booking.customer, user)
        self.assertContains(self.client.get(reverse('account')), chef.name)

    def test_customer_can_cancel_only_their_own_new_bookings(self):
        user = User.objects.create_user('grace@example.com')
        other = User.objects.create_user('peter@example.com')
        chef = make_chef()
        mine = make_booking(chef, customer=user)
        theirs = make_booking(chef, customer=other)
        confirmed = make_booking(chef, customer=user, status='confirmed')
        self.client.force_login(user)

        self.client.post(reverse('cancel_booking', args=[mine.pk]))
        self.assertEqual(self.client.post(reverse('cancel_booking', args=[theirs.pk])).status_code, 404)
        self.client.post(reverse('cancel_booking', args=[confirmed.pk]))

        mine.refresh_from_db(), theirs.refresh_from_db(), confirmed.refresh_from_db()
        self.assertEqual((mine.status, theirs.status, confirmed.status), ('cancelled', 'new', 'confirmed'))

    def test_account_requires_login(self):
        resp = self.client.get(reverse('account'))
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('account')}")


class ChefAccountTests(TestCase):
    def setUp(self):
        self.chef = make_chef()
        self.user = invite_chef(self.chef)

    def test_invite_creates_login_and_emails_set_password_link(self):
        self.assertEqual(self.user.username, 'wanjiru@example.com')
        self.assertEqual(self.chef.user, self.user)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/account/password-reset/', mail.outbox[0].body)

    def test_invite_takes_over_customer_login_with_same_email_and_resets_password(self):
        squatter = User.objects.create_user('amina@example.com', 'amina@example.com', 'guessed-it-99')
        chef = make_chef('Chef Amina', 'amina@example.com')
        self.assertEqual(invite_chef(chef), squatter)
        squatter.refresh_from_db()
        self.assertFalse(squatter.check_password('guessed-it-99'))

    def test_invite_link_lets_chef_set_password(self):
        resp = self.client.get(set_password_path(self.user), follow=True)
        resp = self.client.post(resp.redirect_chain[-1][0], {'new_password1': 'nyama-choma-77', 'new_password2': 'nyama-choma-77'})
        self.assertRedirects(resp, reverse('password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('nyama-choma-77'))

    def test_chef_login_goes_to_dashboard(self):
        self.user.set_password('nyama-choma-77')
        self.user.save()
        resp = self.client.post(reverse('login'), {'username': 'wanjiru@example.com', 'password': 'nyama-choma-77'})
        self.assertRedirects(resp, reverse('chef_dashboard'))

    def test_dashboard_shows_only_own_bookings(self):
        make_booking(self.chef, full_name='Mine Customer')
        make_booking(make_chef('Chef Otieno', 'otieno@example.com'), full_name='Other Customer')
        self.client.force_login(self.user)
        resp = self.client.get(reverse('chef_dashboard'))
        self.assertContains(resp, 'Mine Customer')
        self.assertNotContains(resp, 'Other Customer')

    def test_customer_cannot_open_chef_dashboard(self):
        self.client.force_login(User.objects.create_user('grace@example.com'))
        self.assertRedirects(self.client.get(reverse('chef_dashboard')), reverse('account'))

    def test_confirm_booking_emails_customer(self):
        booking = make_booking(self.chef)
        self.client.force_login(self.user)
        mail.outbox.clear()
        self.client.post(reverse('update_booking_status', args=[booking.pk]), {'status': 'confirmed', 'price': 6000})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')
        self.assertIn('grace@example.com', [m.to[0] for m in mail.outbox])

    def test_status_must_follow_allowed_transitions(self):
        booking = make_booking(self.chef)
        self.client.force_login(self.user)
        self.client.post(reverse('update_booking_status', args=[booking.pk]), {'status': 'completed'})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'new')

    def test_chef_cannot_update_another_chefs_booking(self):
        other = make_booking(make_chef('Chef Otieno', 'otieno@example.com'))
        self.client.force_login(self.user)
        resp = self.client.post(reverse('update_booking_status', args=[other.pk]), {'status': 'confirmed'})
        self.assertEqual(resp.status_code, 404)

    def test_chef_can_edit_profile_and_add_package(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('chef_profile_edit'), {
            'headline': 'New headline', 'bio': 'New bio', 'services': [ServiceCategory.objects.first().pk], 'cuisine': 'kenyan',
            'city': self.chef.city_id, 'area': 'Kilimani', 'years_experience': 5, 'starting_price': 5000,
            'price_unit': 'per event', 'phone': '0712345678',
            'packages-TOTAL_FORMS': 1, 'packages-INITIAL_FORMS': 0,
            'packages-0-name': 'Family lunch', 'packages-0-description': 'For 6', 'packages-0-price': 5000,
            'packages-0-price_unit': 'per event', 'packages-0-is_active': 'on',
        })
        self.assertRedirects(resp, reverse('chef_profile_edit'))
        self.chef.refresh_from_db()
        self.assertEqual(self.chef.headline, 'New headline')
        self.assertEqual(self.chef.packages.get().name, 'Family lunch')

    def test_chef_can_preview_hidden_profile_but_public_cannot(self):
        self.chef.is_active = False
        self.chef.save()
        self.assertEqual(self.client.get(self.chef.get_absolute_url()).status_code, 404)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(self.chef.get_absolute_url()), 'This is your profile')


class HomepageTests(TestCase):
    def test_shows_real_packages_reviews_and_counts_only(self):
        chef = make_chef()
        hidden = make_chef(name='Chef Hidden', email='hidden@example.com', is_active=False)
        ChefPackage.objects.create(chef=chef, name='Sunday family lunch', description='Pilau', price=6000)
        ChefPackage.objects.create(chef=hidden, name='Secret menu', description='-', price=1)
        Review.objects.create(chef=chef, customer_name='Grace', rating=5, comment='Amazing pilau', status='published')
        Review.objects.create(chef=chef, customer_name='Brian', rating=5, comment='Not checked yet')

        resp = self.client.get(reverse('index'))
        self.assertContains(resp, 'Sunday family lunch')
        self.assertContains(resp, f'{chef.get_absolute_url()}?package=')
        self.assertNotContains(resp, 'Secret menu')
        self.assertContains(resp, 'Amazing pilau')
        self.assertNotContains(resp, 'Not checked yet')
        self.assertEqual(resp.context['stats']['chefs'], 1)
        # The old hardcoded demo content is gone
        self.assertNotContains(resp, 'Chef Otieno')
        self.assertNotContains(resp, '20% Off')

    def test_testimonials_hidden_without_reviews(self):
        self.assertNotContains(self.client.get(reverse('index')), 'id="testimonials"')

    def test_chef_match_request_is_saved_and_team_notified(self):
        resp = self.client.post(reverse('request_chef'), {
            'full_name': 'Jane Wanjiku', 'phone': '0712345678', 'email': 'jane@example.com',
            'occasion': 'party', 'guests': '7-15', 'cuisine': '',
            'event_date': (datetime.date.today() + datetime.timedelta(days=3)).isoformat(),
            'time_slot': 'dinner', 'location': 'Kilimani', 'notes': 'No pork',
        }, follow=True)
        match = ChefMatchRequest.objects.get()
        self.assertEqual(match.phone, '+254712345678')
        self.assertContains(resp, 'match you with a chef and get back to you')
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ['hello@simplychefke.com', 'jane@example.com'])

    def test_chef_match_request_rejects_past_date(self):
        resp = self.client.post(reverse('request_chef'), {
            'full_name': 'Jane', 'phone': '0712345678', 'occasion': 'party', 'guests': '7-15',
            'event_date': '2020-01-01', 'time_slot': 'dinner', 'location': 'Kilimani',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, 'Please choose a date from today onwards.', status_code=400)
        self.assertFalse(ChefMatchRequest.objects.exists())

    def test_contact_message_is_saved(self):
        resp = self.client.post(reverse('contact'), {
            'name': 'Brian', 'email': 'brian@example.com', 'phone': '', 'subject': 'events', 'message': 'Office party for 40',
        }, follow=True)
        self.assertEqual(ContactMessage.objects.get().message, 'Office party for 40')
        self.assertContains(resp, 'Message sent!')

    def test_subscribe_once_per_email(self):
        self.client.post(reverse('subscribe'), {'email': 'Fan@Example.com'})
        resp = self.client.post(reverse('subscribe'), {'email': 'fan@example.com'}, follow=True)
        self.assertEqual(Subscriber.objects.get().email, 'fan@example.com')
        self.assertContains(resp, 'already subscribed')

    def test_subscribe_rejects_bad_email(self):
        resp = self.client.post(reverse('subscribe'), {'email': 'not-an-email'})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Subscriber.objects.exists())

    def test_legal_pages_are_linked_from_footer(self):
        resp = self.client.get(reverse('index'))
        self.assertContains(resp, f'href="{reverse("privacy")}"')
        self.assertContains(resp, f'href="{reverse("terms")}"')
        self.assertContains(self.client.get(reverse('privacy')), 'id="cookies"')
        self.assertEqual(self.client.get(reverse('terms')).status_code, 200)

    def test_social_links_only_shown_when_set(self):
        self.assertNotContains(self.client.get(reverse('index')), 'fa-tiktok')
        with self.settings(SOCIAL_LINKS={'tiktok': 'https://www.tiktok.com/@simplychefke'}):
            self.assertContains(self.client.get(reverse('index')), 'https://www.tiktok.com/@simplychefke')


# Uploaded test documents go here instead of the real media folder
TEST_MEDIA = tempfile.mkdtemp()


def tearDownModule():
    shutil.rmtree(TEST_MEDIA, ignore_errors=True)


def make_application(**kwargs):
    return ChefApplication.objects.create(**{
        'full_name': 'Amina Hassan', 'phone': '+254711111111', 'email': 'amina@example.com', 'location': 'Nairobi West',
        'chef_type': 'professional', 'services': 'both', 'cuisine': 'coastal', 'years_experience': 6, 'bio': 'Biryani',
        'national_id': SimpleUploadedFile('id.pdf', b'%PDF'), 'food_handler_certificate': SimpleUploadedFile('cert.pdf', b'%PDF'),
        'agreed_to_terms': True, **kwargs,
    })


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class ChefDashboardToolsTests(TestCase):
    """Food photos, documents and messages with customers."""

    def setUp(self):
        self.chef = make_chef(is_verified=True)
        self.user = invite_chef(self.chef)
        self.client.force_login(self.user)
        mail.outbox.clear()

    def photo_data(self, *new, **existing):
        photos = list(self.chef.photos.all())
        data = {'photos-TOTAL_FORMS': len(photos), 'photos-INITIAL_FORMS': len(photos), 'new_photos': list(new)}
        for i, photo in enumerate(photos):
            data[f'photos-{i}-id'] = photo.pk
            data[f'photos-{i}-caption'] = existing.get(f'caption{i}', photo.caption)
            if existing.get(f'delete{i}'):
                data[f'photos-{i}-DELETE'] = 'on'
        return data

    def test_add_several_photos_at_once_then_caption_and_remove(self):
        resp = self.client.post(reverse('chef_photos'), self.photo_data(dish_photo('a.png'), dish_photo('b.png'), dish_photo('c.png')))
        self.assertRedirects(resp, reverse('chef_photos'))
        self.assertEqual(self.chef.photos.count(), 3)

        self.client.post(reverse('chef_photos'), self.photo_data(caption0='Pilau', delete1=True))
        self.assertEqual(self.chef.photos.count(), 2)
        self.assertTrue(self.chef.photos.filter(caption='Pilau').exists())

    def test_photos_are_capped_at_twelve(self):
        for i in range(11):
            self.chef.photos.create(image=f'chefs/gallery/{i}.png')
        resp = self.client.post(reverse('chef_photos'), self.photo_data(dish_photo('a.png'), dish_photo('b.png')))
        self.assertContains(resp, 'up to 12 photos', status_code=400)
        self.assertEqual(self.chef.photos.count(), 11)
        # Removing one makes room for two
        self.client.post(reverse('chef_photos'), self.photo_data(dish_photo('a.png'), dish_photo('b.png'), delete0=True))
        self.assertEqual(self.chef.photos.count(), 12)

    def test_size_limit_is_shown_and_enforced_for_new_photos(self):
        self.assertContains(self.client.get(reverse('chef_photos')), 'JPG or PNG, up to 5 MB each.')
        big = SimpleUploadedFile('big.png', dish_photo('big.png').read() + b'\0' * 5 * 1024 * 1024, content_type='image/png')
        resp = self.client.post(reverse('chef_photos'), self.photo_data(big, dish_photo('a.png')))
        self.assertContains(resp, 'File must be smaller than 5 MB.', status_code=400)
        self.assertEqual(self.chef.photos.count(), 0)

    def test_new_document_unverifies_chef_and_tells_team(self):
        resp = self.client.post(reverse('chef_documents'), {'national_id': SimpleUploadedFile('id.pdf', b'%PDF')})
        self.assertRedirects(resp, reverse('chef_documents'))
        self.chef.refresh_from_db()
        self.assertTrue(self.chef.national_id.name.startswith('chefs/documents/ids/'))
        self.assertFalse(self.chef.is_verified)
        self.assertIsNotNone(self.chef.documents_updated_at)
        self.assertTrue(any('uploaded new documents' in m.subject for m in mail.outbox))

    def test_documents_need_a_file_of_the_right_type(self):
        self.assertContains(self.client.post(reverse('chef_documents'), {}), 'Choose a new file', status_code=400)
        resp = self.client.post(reverse('chef_documents'), {'national_id': SimpleUploadedFile('id.exe', b'MZ')})
        self.assertEqual(resp.status_code, 400)
        self.chef.refresh_from_db()
        self.assertTrue(self.chef.is_verified)

    def test_approving_an_application_copies_its_documents(self):
        application = make_application()
        chef = create_chef_profile(application)
        self.assertEqual(chef.national_id.name, application.national_id.name)
        self.assertEqual(chef.food_handler_certificate.name, application.food_handler_certificate.name)

    def test_chef_messages_customer_who_replies_from_booking_page(self):
        booking = make_booking(self.chef)
        resp = self.client.post(reverse('chef_booking', args=[booking.pk]), {'body': 'Any allergies?'})
        self.assertRedirects(resp, f"{reverse('chef_booking', args=[booking.pk])}#messages", fetch_redirect_response=False)
        to_customer = mail.outbox[-1]
        self.assertEqual(to_customer.to, ['grace@example.com'])
        self.assertIn('Any allergies?', to_customer.body)
        self.assertIn(f'/bookings/{booking.pk}/?key=', to_customer.body)

        # The customer opens the link from the email and replies
        customer = Client()
        self.assertContains(customer.get(booking.customer_url()), 'Any allergies?')
        customer.post(reverse('booking_confirmation', args=[booking.pk]), {'body': 'No nuts please'})
        self.assertEqual([m.from_chef for m in booking.messages.all()], [True, False])
        self.assertEqual(mail.outbox[-1].to, ['wanjiru@example.com'])
        self.assertIn(f'/chef/bookings/{booking.pk}/', mail.outbox[-1].body)
        self.assertContains(self.client.get(reverse('chef_booking', args=[booking.pk])), 'No nuts please')
        self.assertContains(self.client.get(reverse('chef_dashboard')), 'Messages (2)')

    def test_messages_stay_between_the_chef_and_the_customer(self):
        other = make_booking(make_chef('Chef Otieno', 'otieno@example.com'))
        self.assertEqual(self.client.get(reverse('chef_booking', args=[other.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('chef_booking', args=[other.pk]), {'body': 'Hi'}).status_code, 404)
        self.assertEqual(Client().post(reverse('booking_confirmation', args=[other.pk]), {'body': 'Hi'}).status_code, 404)
        self.assertFalse(other.messages.exists())

    def test_customer_messages_through_the_api(self):
        booking = make_booking(self.chef)
        booking.messages.create(from_chef=True, body='Any allergies?')
        key = booking.customer_url().split('key=')[1]
        customer = Client()
        self.assertEqual(customer.post(f'/api/bookings/{booking.pk}/messages/', {'body': 'Hi'}).status_code, 404)
        data = customer.get(f'/api/bookings/{booking.pk}/?key={key}').json()
        self.assertEqual([(m['from_chef'], m['body']) for m in data['messages']], [(True, 'Any allergies?')])

        self.assertEqual(customer.post(f'/api/bookings/{booking.pk}/messages/?key={key}', {'body': ''}).status_code, 400)
        resp = customer.post(f'/api/bookings/{booking.pk}/messages/?key={key}', {'body': 'No nuts please'})
        self.assertEqual(resp.json()['redirect'], f'/bookings/{booking.pk}/#messages')
        self.assertEqual(booking.messages.last().body, 'No nuts please')

    def test_chef_and_team_pages_load(self):
        booking = make_booking(self.chef)
        booking.messages.create(from_chef=False, body='Hello chef')
        for name, args in [('chef_dashboard', []), ('chef_booking', [booking.pk]), ('chef_photos', []),
                           ('chef_documents', []), ('chef_profile_edit', [])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)
        self.client.force_login(User.objects.create_user('team@example.com', is_staff=True))
        self.assertContains(self.client.get(reverse('team_booking', args=[booking.pk])), 'Hello chef')
        self.assertEqual(self.client.get(reverse('team_chefs') + '?show=documents').status_code, 200)
        self.client.post(reverse('team_chef_verified', args=[self.chef.pk]), {'verified': '0'})
        self.chef.refresh_from_db()
        self.assertFalse(self.chef.is_verified)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class TeamPagesTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('team@example.com', 'team@example.com', 'pw', is_staff=True)
        self.client.force_login(self.staff)

    def test_team_pages_are_staff_only(self):
        self.client.force_login(User.objects.create_user('grace@example.com'))
        self.assertEqual(self.client.get(reverse('team_home')).status_code, 302)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('team_bookings')).status_code, 302)

    def test_every_team_page_loads(self):
        application = make_application()
        make_booking(make_chef())
        ChefMatchRequest.objects.create(
            full_name='Jane', phone='+254712345678', occasion='party', guests='7-15',
            event_date=datetime.date.today(), time_slot='dinner', location='Kilimani',
        )
        ContactMessage.objects.create(name='Brian', email='brian@example.com', subject='events', message='Hello')
        for name, args in [('team_home', []), ('team_applications', []), ('team_application', [application.pk]),
                           ('team_bookings', []), ('team_requests', []), ('team_inbox', [])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)

    def test_staff_login_lands_on_team_home(self):
        self.client.logout()
        self.staff.set_password('team-pass-77')
        self.staff.save()
        resp = self.client.post(reverse('login'), {'username': 'team@example.com', 'password': 'team-pass-77'})
        self.assertRedirects(resp, reverse('team_home'))

    def test_approve_creates_hidden_profile_and_sends_one_welcome_email_with_login(self):
        application = make_application()
        self.client.post(reverse('team_approve_application', args=[application.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        chef = application.chef
        self.assertFalse(chef.is_active)
        self.assertEqual(chef.user.username, 'amina@example.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('approved', mail.outbox[0].subject)
        self.assertIn('/account/password-reset/', mail.outbox[0].body)

    def test_approving_twice_does_not_create_a_second_profile(self):
        application = make_application()
        self.client.post(reverse('team_approve_application', args=[application.pk]))
        self.client.post(reverse('team_approve_application', args=[application.pk]))
        self.assertEqual(Chef.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_approve_puts_welcome_message_in_email(self):
        application = make_application()
        self.client.post(reverse('team_approve_application', args=[application.pk]), {'message': 'Karibu sana, Amina!'})
        application.refresh_from_db()
        self.assertEqual(application.decision_message, 'Karibu sana, Amina!')
        self.assertIn('Karibu sana, Amina!', mail.outbox[0].body)

    def test_reject_emails_applicant_with_reason(self):
        application = make_application()
        self.client.post(reverse('team_reject_application', args=[application.pk]), {'reason': 'Your certificate has expired.'})
        application.refresh_from_db()
        self.assertEqual(application.status, 'rejected')
        self.assertEqual(application.decision_message, 'Your certificate has expired.')
        self.assertEqual(mail.outbox[0].to, ['amina@example.com'])
        self.assertIn('Your certificate has expired.', mail.outbox[0].body)

    def test_reject_needs_a_reason(self):
        application = make_application()
        self.client.post(reverse('team_reject_application', args=[application.pk]), {'reason': ''})
        application.refresh_from_db()
        self.assertEqual(application.status, 'pending')
        self.assertEqual(len(mail.outbox), 0)

    def test_put_chef_live(self):
        chef = make_chef(is_active=False)
        self.client.post(reverse('team_chef_live', args=[chef.pk]), {'live': '1'})
        chef.refresh_from_db()
        self.assertTrue(chef.is_active)

    def test_team_confirming_booking_emails_customer_and_chef_not_team(self):
        chef = make_chef()
        invite_chef(chef)
        booking = make_booking(chef)
        mail.outbox.clear()
        self.client.post(reverse('team_booking_status', args=[booking.pk]), {'status': 'confirmed', 'price': 6000})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ['grace@example.com', 'wanjiru@example.com'])
        self.assertIn('confirmed your booking', next(m.body for m in mail.outbox if m.to == ['grace@example.com']))

    def test_request_and_message_status(self):
        match = ChefMatchRequest.objects.create(
            full_name='Jane', phone='+254712345678', occasion='party', guests='7-15',
            event_date=datetime.date.today(), time_slot='dinner', location='Kilimani',
        )
        msg = ContactMessage.objects.create(name='Brian', email='brian@example.com', subject='events', message='Hello')
        self.client.post(reverse('team_request_status', args=[match.pk]), {'status': 'matched'})
        self.client.post(reverse('team_message_replied', args=[msg.pk]))
        match.refresh_from_db(), msg.refresh_from_db()
        self.assertEqual((match.status, msg.is_handled), ('matched', True))


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class AdminEmailTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser('boss', 'boss@example.com', 'pw'))

    def test_admin_approve_action_asks_for_welcome_message_then_emails_login(self):
        application = make_application()
        url = reverse('admin:SimplyChefKe_chefapplication_changelist')
        data = {'action': 'approve', '_selected_action': [application.pk]}
        self.assertContains(self.client.post(url, data), 'Welcome message to the chef')
        self.assertEqual(len(mail.outbox), 0)
        self.client.post(url, {**data, 'apply': '1', 'message': 'Welcome aboard!'})
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        self.assertTrue(hasattr(application, 'chef'))
        self.assertEqual([m.to for m in mail.outbox], [['amina@example.com']])
        self.assertIn('Welcome aboard!', mail.outbox[0].body)

    def test_admin_reject_action_asks_for_reason_then_emails_applicant(self):
        application = make_application()
        url = reverse('admin:SimplyChefKe_chefapplication_changelist')
        data = {'action': 'reject', '_selected_action': [application.pk]}
        self.assertContains(self.client.post(url, data), 'Reason for rejection')
        self.client.post(url, {**data, 'apply': '1', 'reason': ''})
        self.assertEqual(len(mail.outbox), 0)
        self.client.post(url, {**data, 'apply': '1', 'reason': 'We are full in your area for now.'})
        self.assertEqual([m.to for m in mail.outbox], [['amina@example.com']])
        self.assertIn('We are full in your area for now.', mail.outbox[0].body)

    def test_admin_status_change_on_booking_emails_customer(self):
        booking = make_booking(make_chef())
        resp = self.client.post(reverse('admin:SimplyChefKe_bookingrequest_change', args=[booking.pk]), {
            'chef': booking.chef_id, 'full_name': booking.full_name, 'phone': booking.phone, 'email': booking.email,
            'event_date': booking.event_date.isoformat(), 'time_slot': booking.time_slot, 'guests': booking.guests,
            'location': booking.location, 'notes': '', 'status': 'confirmed', 'package': '', 'customer': '',
            'price': 6000, 'payment_status': 'unpaid', 'mpesa_code': '', 'team_notes': '',
            'messages-TOTAL_FORMS': 0, 'messages-INITIAL_FORMS': 0,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertIn(['grace@example.com'], [m.to for m in mail.outbox])


class RemovedAppTests(TestCase):
    def test_service_worker_removes_itself(self):
        sw = self.client.get(reverse('service_worker'))
        self.assertEqual(sw['Content-Type'], 'application/javascript')
        self.assertContains(sw, 'self.registration.unregister()')

    def test_pages_are_not_installable(self):
        page = self.client.get(reverse('index'))
        self.assertNotContains(page, 'rel="manifest"')
        self.assertNotContains(page, 'data-install-app')


def dish_photo(name):
    buf = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(buf, 'PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


def application_data(**kwargs):
    return {
        'full_name': 'Amina Hassan', 'phone': '0711111111', 'email': 'amina@example.com', 'location': 'Nairobi West',
        'chef_type': 'professional', 'services': 'both', 'cuisine': 'coastal', 'years_experience': 6, 'bio': 'Biryani',
        'national_id': SimpleUploadedFile('id.pdf', b'%PDF'), 'food_handler_certificate': SimpleUploadedFile('cert.pdf', b'%PDF'),
        'dish_photos': [dish_photo(f'dish{n}.png') for n in range(3)], 'agreed_to_terms': 'on', **kwargs,
    }


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class BecomeChefPageTests(TestCase):
    application_data = staticmethod(application_data)

    def test_page_shows_the_application_form(self):
        resp = self.client.get(reverse('become_chef'))
        self.assertTemplateUsed(resp, 'become_a_chef.html')
        self.assertContains(resp, 'Submit Application')
        self.assertContains(self.client.get(reverse('login'), {'role': 'chef'}), f'href="{reverse("become_chef")}"')

    def test_application_is_saved_and_thank_you_shown(self):
        resp = self.client.post(reverse('become_chef'), self.application_data(), follow=True)
        self.assertRedirects(resp, f"{reverse('become_chef')}?sent=1")
        self.assertContains(resp, 'Application received!')
        self.assertNotContains(resp, 'Submit Application')
        application = ChefApplication.objects.get()
        self.assertEqual((application.phone, application.dish_photos.count()), ('+254711111111', 3))

    def test_errors_are_shown_on_the_page(self):
        resp = self.client.post(reverse('become_chef'), self.application_data(dish_photos=[dish_photo('one.png')]))
        self.assertEqual(resp.status_code, 400)
        self.assertTemplateUsed(resp, 'become_a_chef.html')
        self.assertContains(resp, 'Please upload between 3 and 5 photos.', status_code=400)
        self.assertFalse(ChefApplication.objects.exists())

    def test_size_limit_is_shown_and_enforced_for_dish_photos(self):
        self.assertContains(self.client.get(reverse('become_chef')), 'JPG or PNG, up to 5 MB each.')
        big = SimpleUploadedFile('big.png', dish_photo('big.png').read() + b'\0' * 5 * 1024 * 1024, content_type='image/png')
        resp = self.client.post(reverse('become_chef'), self.application_data(dish_photos=[big, *self.application_data()['dish_photos'][:2]]))
        self.assertContains(resp, 'File must be smaller than 5 MB.', status_code=400)
        self.assertFalse(ChefApplication.objects.exists())


class BookingPageTests(TestCase):
    def setUp(self):
        self.chef = make_chef()
        self.package = ChefPackage.objects.create(chef=self.chef, name='Sunday family lunch', description='Pilau', price=6000)
        self.data = {
            'package': self.package.pk, 'full_name': 'Grace Muthoni', 'phone': '0712345678', 'email': 'grace@example.com',
            'event_date': datetime.date.today() + datetime.timedelta(days=5), 'time_slot': 'lunch', 'guests': 4,
            'location': 'Kileleshwa',
        }

    def test_booking_page_preselects_package(self):
        resp = self.client.get(reverse('book_chef', args=[self.chef.slug]) + f'?package={self.package.pk}')
        self.assertTemplateUsed(resp, 'booking.html')
        self.assertContains(resp, f'<option value="{self.package.pk}" selected>')

    def test_hidden_chef_cannot_be_booked(self):
        hidden = make_chef(name='Chef Hidden', email='hidden@example.com', is_active=False)
        self.assertEqual(self.client.get(reverse('book_chef', args=[hidden.slug])).status_code, 404)

    def test_guest_booking_redirects_to_confirmation_only_they_can_see(self):
        resp = self.client.post(reverse('book_chef', args=[self.chef.slug]), self.data, follow=True)
        booking = BookingRequest.objects.get()
        self.assertRedirects(resp, reverse('booking_confirmation', args=[booking.pk]))
        self.assertTemplateUsed(resp, 'booking_confirmation.html')
        self.assertContains(resp, 'Booking request <span>sent!</span>', html=False)
        self.assertContains(resp, 'Sunday family lunch')

        # Someone else's browser can't open it
        self.client.logout()
        self.assertEqual(self.client.get(reverse('booking_confirmation', args=[booking.pk])).status_code, 404)

    def test_customer_sees_their_own_booking_but_not_others(self):
        user = User.objects.create_user('grace@example.com')
        other = User.objects.create_user('peter@example.com')
        mine, theirs = make_booking(self.chef, customer=user), make_booking(self.chef, customer=other)
        self.client.force_login(user)
        self.assertContains(self.client.get(reverse('account')), reverse('booking_confirmation', args=[mine.pk]))
        self.assertContains(self.client.get(reverse('booking_confirmation', args=[mine.pk])), 'My bookings')
        self.assertEqual(self.client.get(reverse('booking_confirmation', args=[theirs.pk])).status_code, 404)

    def test_errors_from_profile_form_are_shown_on_booking_page(self):
        resp = self.client.post(reverse('book_chef', args=[self.chef.slug]), {**self.data, 'event_date': '2020-01-01'})
        self.assertEqual(resp.status_code, 400)
        self.assertTemplateUsed(resp, 'booking.html')
        self.assertContains(resp, 'Please choose a date from today onwards.', status_code=400)
        self.assertFalse(BookingRequest.objects.exists())


def in_days(n):
    return datetime.date.today() + datetime.timedelta(days=n)


class AvailabilityTests(TestCase):
    def setUp(self):
        self.chef = make_chef()
        self.user = invite_chef(self.chef)
        self.data = {
            'full_name': 'Grace Muthoni', 'phone': '0712345678', 'event_date': in_days(5), 'time_slot': 'dinner',
            'guests': 4, 'location': 'Kileleshwa',
        }

    def book(self, **kwargs):
        return self.client.post(reverse('book_chef', args=[self.chef.slug]), {**self.data, **kwargs})

    def test_cannot_book_a_day_the_chef_is_away(self):
        ChefTimeOff.objects.create(chef=self.chef, start_date=in_days(4), end_date=in_days(6))
        resp = self.book()
        self.assertContains(resp, 'is away on', status_code=400)
        self.assertFalse(BookingRequest.objects.exists())
        self.assertEqual(self.book(event_date=in_days(7)).status_code, 302)

    def test_cannot_book_a_slot_already_confirmed(self):
        make_booking(self.chef, event_date=in_days(5), time_slot='dinner', status='confirmed')
        self.assertContains(self.book(), 'already booked for this time', status_code=400)
        self.assertEqual(self.book(time_slot='lunch').status_code, 302)

    def test_paused_chef_cannot_be_booked_but_profile_stays_visible(self):
        self.chef.is_accepting_bookings = False
        self.chef.save()
        self.assertContains(self.book(), 'not taking new bookings', status_code=400)
        resp = self.client.get(self.chef.get_absolute_url())
        self.assertContains(resp, 'is not taking new bookings right now')
        self.assertNotContains(resp, 'Send Booking Request')

    def test_paused_packages_are_hidden_and_cannot_be_booked(self):
        paused = ChefPackage.objects.create(chef=self.chef, name='Christmas feast', description='-', price=9000, is_active=False)
        ChefPackage.objects.create(chef=self.chef, name='Sunday lunch', description='-', price=5000)
        resp = self.client.get(self.chef.get_absolute_url())
        self.assertContains(resp, 'Sunday lunch')
        self.assertNotContains(resp, 'Christmas feast')
        self.assertEqual(self.book(package=paused.pk).status_code, 400)

    def test_chef_adds_single_day_off_and_removes_it(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('chef_availability'), {'start_date': in_days(3), 'end_date': '', 'note': 'Wedding'})
        self.assertRedirects(resp, reverse('chef_availability'))
        time_off = self.chef.time_off.get()
        self.assertEqual(time_off.end_date, in_days(3))
        # Away dates show publicly, the private note does not
        resp = self.client.get(self.chef.get_absolute_url())
        self.assertContains(resp, 'Away:')
        self.assertNotContains(resp, 'Wedding')

        self.client.post(reverse('chef_time_off_delete', args=[time_off.pk]))
        self.assertFalse(self.chef.time_off.exists())

    def test_time_off_end_must_not_be_before_start(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('chef_availability'), {'start_date': in_days(5), 'end_date': in_days(3)})
        self.assertContains(resp, 'on or after the first day', status_code=400)

    def test_chef_cannot_remove_another_chefs_time_off(self):
        other = ChefTimeOff.objects.create(chef=make_chef('Chef Otieno', 'otieno@example.com'), start_date=in_days(1), end_date=in_days(1))
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('chef_time_off_delete', args=[other.pk])).status_code, 404)

    def test_chef_pauses_and_resumes_bookings(self):
        self.client.force_login(self.user)
        self.client.post(reverse('chef_availability'), {'accepting': '0'})
        self.chef.refresh_from_db()
        self.assertFalse(self.chef.is_accepting_bookings)
        self.client.post(reverse('chef_availability'), {'accepting': '1'})
        self.chef.refresh_from_db()
        self.assertTrue(self.chef.is_accepting_bookings)

    def test_confirming_needs_a_price_and_a_free_slot(self):
        booking = make_booking(self.chef)
        self.client.force_login(self.user)
        url = reverse('update_booking_status', args=[booking.pk])

        self.client.post(url, {'status': 'confirmed'})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'new')

        make_booking(self.chef, status='confirmed', full_name='Earlier Customer')
        self.client.post(url, {'status': 'confirmed', 'price': 7000})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'new')

    def test_per_person_package_suggests_price_for_all_guests(self):
        package = ChefPackage.objects.create(chef=self.chef, name='Buffet', description='-', price=950, price_unit='per guest')
        self.assertEqual(make_booking(self.chef, package=package, guests=20).suggested_price, 19000)


@override_settings(MPESA_PAYBILL='247247')
class PaymentTests(TestCase):
    def setUp(self):
        self.chef = make_chef()
        invite_chef(self.chef)
        self.booking = make_booking(self.chef)
        self.staff = User.objects.create_user('team@example.com', 'team@example.com', 'pw', is_staff=True)
        mail.outbox.clear()

    def confirm(self, price=6000):
        self.client.force_login(self.staff)
        self.client.post(reverse('team_booking_status', args=[self.booking.pk]), {'status': 'confirmed', 'price': price})
        self.client.logout()
        self.booking.refresh_from_db()

    def test_confirmation_email_has_price_and_a_pay_link_that_works_for_guests(self):
        self.confirm()
        self.assertEqual(self.booking.price, 6000)
        body = next(m.body for m in mail.outbox if m.to == ['grace@example.com'])
        self.assertIn('KSh 6,000', body)
        pay_url = body.split('Pay by M-Pesa here: ')[1].split()[0].removeprefix(settings.SITE_URL)

        resp = self.client.get(pay_url)
        self.assertContains(resp, '247247')
        self.assertContains(resp, self.booking.payment_reference)
        # The key is remembered, so the page's own links work too
        self.assertEqual(self.client.get(reverse('booking_confirmation', args=[self.booking.pk])).status_code, 200)

    def test_bad_or_missing_key_is_not_found(self):
        self.confirm()
        url = reverse('booking_checkout', args=[self.booking.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(url + '?key=forged').status_code, 404)
        other = make_booking(self.chef)
        self.assertEqual(self.client.get(f"{url}?key={other.customer_url().split('key=')[1]}").status_code, 404)

    def test_customer_submits_mpesa_code_and_team_is_told(self):
        self.confirm()
        mail.outbox.clear()
        url = self.booking.customer_url('booking_checkout')
        resp = self.client.post(url, {'mpesa_code': 'sjk4h7l2qp'})
        self.assertRedirects(resp, reverse('booking_confirmation', args=[self.booking.pk]))
        self.booking.refresh_from_db()
        self.assertEqual((self.booking.payment_status, self.booking.mpesa_code), ('submitted', 'SJK4H7L2QP'))
        self.assertEqual([m.to for m in mail.outbox], [['hello@simplychefke.com']])
        # Can't pay twice
        self.assertRedirects(self.client.get(url), reverse('booking_confirmation', args=[self.booking.pk]))

    def test_mpesa_code_must_be_valid_and_unused(self):
        self.confirm()
        make_booking(self.chef, mpesa_code='SJK4H7L2QP', time_slot='lunch')
        url = self.booking.customer_url('booking_checkout')
        self.assertContains(self.client.post(url, {'mpesa_code': 'abc'}), '10 letters and numbers', status_code=400)
        self.assertContains(self.client.post(url, {'mpesa_code': 'SJK4H7L2QP'}), 'already been used', status_code=400)

    def test_cannot_pay_before_chef_confirms(self):
        url = self.booking.customer_url('booking_checkout')
        self.assertRedirects(self.client.get(url), reverse('booking_confirmation', args=[self.booking.pk]))

    def test_team_marks_payment_received_and_customer_and_chef_are_emailed(self):
        self.confirm()
        self.booking.payment_status, self.booking.mpesa_code = 'submitted', 'SJK4H7L2QP'
        self.booking.save()
        mail.outbox.clear()
        self.client.force_login(self.staff)
        self.client.post(reverse('team_booking_payment', args=[self.booking.pk]), {'payment_status': 'paid'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, 'paid')
        self.assertIsNotNone(self.booking.paid_at)
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ['grace@example.com', 'wanjiru@example.com'])

    def test_payment_not_found_clears_the_code_so_customer_can_try_again(self):
        self.confirm()
        self.booking.payment_status, self.booking.mpesa_code = 'submitted', 'SJK4H7L2QP'
        self.booking.save()
        self.client.force_login(self.staff)
        self.client.post(reverse('team_booking_payment', args=[self.booking.pk]), {'payment_status': 'unpaid'})
        self.booking.refresh_from_db()
        self.assertEqual((self.booking.payment_status, self.booking.mpesa_code), ('unpaid', ''))
        self.assertTrue(self.booking.customer_can_pay)

    def test_refund_only_after_cancelling_a_paid_booking(self):
        self.confirm()
        self.booking.payment_status = 'paid'
        self.booking.save()
        self.client.force_login(self.staff)
        url = reverse('team_booking_payment', args=[self.booking.pk])
        self.client.post(url, {'payment_status': 'refunded'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, 'paid')

        self.client.post(reverse('team_booking_status', args=[self.booking.pk]), {'status': 'cancelled'})
        self.client.post(url, {'payment_status': 'refunded'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, 'refunded')

    def test_chef_cancelling_a_paid_booking_tells_team_to_refund(self):
        self.confirm()
        self.booking.payment_status = 'paid'
        self.booking.save()
        mail.outbox.clear()
        self.client.force_login(self.chef.user)
        self.client.post(reverse('update_booking_status', args=[self.booking.pk]), {'status': 'cancelled'})
        team_mail = next(m for m in mail.outbox if m.to == ['hello@simplychefke.com'])
        self.assertIn('refund them', team_mail.body)

    def test_unpaid_confirmed_booking_shows_pay_button(self):
        self.confirm()
        resp = self.client.get(self.booking.customer_url())
        self.assertContains(resp, 'Pay KSh 6,000 with M-Pesa')


class ReviewTests(TestCase):
    def setUp(self):
        self.chef = make_chef()
        invite_chef(self.chef)
        self.booking = make_booking(self.chef, status='completed')
        self.review_url = self.booking.customer_url('booking_review')
        self.data = {'customer_name': 'Grace', 'rating': 5, 'comment': 'The pilau was perfect'}
        mail.outbox.clear()

    def test_review_from_completed_booking_waits_for_team(self):
        resp = self.client.post(self.review_url, self.data)
        self.assertRedirects(resp, reverse('booking_confirmation', args=[self.booking.pk]))
        review = Review.objects.get()
        self.assertEqual((review.booking, review.chef, review.status), (self.booking, self.chef, 'pending'))
        self.assertEqual([m.to for m in mail.outbox], [['hello@simplychefke.com']])
        self.assertNotContains(self.client.get(self.chef.get_absolute_url()), 'The pilau was perfect')

    def test_only_one_review_per_booking(self):
        self.client.post(self.review_url, self.data)
        self.client.post(self.review_url, {**self.data, 'comment': 'Again'})
        self.assertEqual(Review.objects.count(), 1)

    def test_cannot_review_before_the_booking_is_completed(self):
        upcoming = make_booking(self.chef, status='confirmed')
        resp = self.client.post(upcoming.customer_url('booking_review'), self.data)
        self.assertRedirects(resp, reverse('booking_confirmation', args=[upcoming.pk]))
        self.assertFalse(Review.objects.exists())

    def test_completed_email_links_to_the_review_page(self):
        booking = make_booking(self.chef, status='confirmed', price=5000)
        staff = User.objects.create_user('team@example.com', is_staff=True)
        self.client.force_login(staff)
        self.client.post(reverse('team_booking_status', args=[booking.pk]), {'status': 'completed'})
        body = next(m.body for m in mail.outbox if m.to == ['grace@example.com'])
        self.assertIn(f'/bookings/{booking.pk}/review/?key=', body)

    def test_team_publishes_review_and_chef_is_emailed(self):
        self.client.post(self.review_url, self.data)
        review = Review.objects.get()
        mail.outbox.clear()
        self.client.force_login(User.objects.create_user('team@example.com', is_staff=True))
        self.client.post(reverse('team_review_status', args=[review.pk]), {'status': 'published'})
        review.refresh_from_db()
        self.assertEqual(review.status, 'published')
        self.assertEqual([m.to for m in mail.outbox], [['wanjiru@example.com']])
        self.assertContains(self.client.get(self.chef.get_absolute_url()), 'The pilau was perfect')

    def test_logged_in_customer_sees_review_button_on_chef_profile(self):
        user = User.objects.create_user('grace@example.com')
        self.booking.customer = user
        self.booking.save()
        self.client.force_login(user)
        self.assertContains(self.client.get(self.chef.get_absolute_url()), reverse('booking_review', args=[self.booking.pk]))


class ReminderTests(TestCase):
    def test_reminds_tomorrows_confirmed_bookings_once(self):
        chef = make_chef()
        invite_chef(chef)
        tomorrow = make_booking(chef, status='confirmed', event_date=in_days(1), price=5000)
        make_booking(chef, status='new', event_date=in_days(1), time_slot='lunch')
        make_booking(chef, status='confirmed', event_date=in_days(2))
        mail.outbox.clear()

        call_command('send_booking_reminders', stdout=io.StringIO())
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ['grace@example.com', 'wanjiru@example.com'])
        self.assertIn('Pay KSh 5,000', next(m.body for m in mail.outbox if m.to == ['grace@example.com']))
        tomorrow.refresh_from_db()
        self.assertIsNotNone(tomorrow.reminder_sent_at)

        mail.outbox.clear()
        call_command('send_booking_reminders', stdout=io.StringIO())
        self.assertEqual(mail.outbox, [])


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class TeamModerationTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user('team@example.com', is_staff=True))

    def test_new_team_pages_load(self):
        chef = make_chef()
        booking = make_booking(chef, status='completed', price=5000)
        Review.objects.create(chef=chef, booking=booking, customer_name='Grace', rating=4, comment='Nice')
        for name, args in [('team_booking', [booking.pk]), ('team_reviews', []), ('team_chefs', [])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)
        self.assertContains(self.client.get(f"{reverse('team_bookings')}?payment=submitted&status="), 'Payments to check')

    def test_team_saves_price_and_private_notes(self):
        booking = make_booking(make_chef())
        self.client.post(reverse('team_booking', args=[booking.pk]), {'price': 8000, 'team_notes': 'Moved to 7 PM'})
        booking.refresh_from_db()
        self.assertEqual((booking.price, booking.team_notes), (8000, 'Moved to 7 PM'))

    def test_feature_chef_on_homepage(self):
        chef = make_chef()
        self.client.post(reverse('team_chef_featured', args=[chef.pk]), {'featured': '1'})
        chef.refresh_from_db()
        self.assertTrue(chef.is_featured)

    def test_team_home_counts_payments_and_reviews_waiting(self):
        chef = make_chef()
        make_booking(chef, status='confirmed', price=5000, payment_status='submitted', mpesa_code='SJK4H7L2QP')
        Review.objects.create(chef=chef, customer_name='Grace', rating=4, comment='Nice')
        waiting = self.client.get(reverse('team_home')).context['waiting']
        self.assertEqual((waiting['payments'], waiting['reviews']), (1, 1))


class ErrorPageTests(TestCase):
    def test_404_page_uses_site_layout(self):
        resp = self.client.get('/no-such-page/')
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, "We can't find", status_code=404)
        self.assertContains(resp, reverse('marketplace'), status_code=404)

    def test_500_page_renders_without_request_context(self):
        html = render_to_string('500.html')
        self.assertIn('Something went', html)

    def test_csrf_failure_page(self):
        client = Client(enforce_csrf_checks=True)
        resp = client.post(reverse('contact'), {'name': 'Brian'})
        self.assertContains(resp, 'Please <span>try again</span>', status_code=403)


class ApiTests(TestCase):
    def setUp(self):
        self.service = ServiceCategory.objects.first()
        self.chef = make_chef(is_featured=True, area='Kilimani')
        self.chef.services.add(self.service)
        ChefPackage.objects.create(chef=self.chef, service=self.service, name='Dinner for 6', description='3 courses', price=9000)
        ChefPackage.objects.create(chef=self.chef, name='Old package', description='Gone', price=1, is_active=False)
        self.hidden = make_chef(name='Chef Hidden', email='hidden@example.com', is_active=False)
        Review.objects.create(chef=self.chef, customer_name='Grace', rating=5, comment='Amazing', status=Review.Status.PUBLISHED)
        Review.objects.create(chef=self.chef, customer_name='Brian', rating=3, comment='Ok', status=Review.Status.PUBLISHED)
        Review.objects.create(chef=self.chef, customer_name='Spam', rating=1, comment='Not checked yet')

    def test_chef_list_shows_live_chefs_without_contact_details(self):
        resp = self.client.get('/api/chefs/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['count'], 1)
        chef = data['results'][0]
        self.assertEqual(chef['slug'], self.chef.slug)
        self.assertEqual((chef['avg_rating'], chef['review_count']), (4.0, 2))
        self.assertTrue(chef['photo'].startswith('http://testserver/'))
        self.assertNotIn('phone', chef)
        self.assertNotIn('email', chef)

    def test_chef_list_uses_marketplace_filters(self):
        other_city = City.objects.create(name='Test Town', slug='test-town', order=99)
        Chef.objects.filter(pk=make_chef(name='Chef Amina', email='amina@example.com').pk).update(city=other_city)
        self.assertEqual(self.client.get('/api/chefs/?city=test-town').json()['count'], 1)
        self.assertEqual(self.client.get(f'/api/chefs/?service={self.service.slug}').json()['count'], 1)
        self.assertEqual(self.client.get('/api/chefs/?q=dinner for').json()['count'], 1)
        self.assertEqual(self.client.get('/api/chefs/?featured=1').json()['count'], 1)
        prices = [c['starting_price'] for c in self.client.get('/api/chefs/?sort=price_high').json()['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_chef_detail_shows_only_offered_packages_and_private_dates_without_notes(self):
        ChefTimeOff.objects.create(
            chef=self.chef, start_date=datetime.date.today(), end_date=datetime.date.today(), note='Family wedding',
        )
        data = self.client.get(f'/api/chefs/{self.chef.slug}/').json()
        self.assertEqual([p['name'] for p in data['packages']], ['Dinner for 6'])
        self.assertEqual(len(data['time_off']), 1)
        self.assertNotIn('note', data['time_off'][0])
        self.assertNotIn('phone', data)

    def test_hidden_chef_is_not_found_except_by_its_owner(self):
        self.assertEqual(self.client.get(f'/api/chefs/{self.hidden.slug}/').status_code, 404)
        self.hidden.user = User.objects.create_user('hidden@example.com', 'hidden@example.com', 'pass12345!')
        self.hidden.save()
        self.client.force_login(self.hidden.user)
        self.assertEqual(self.client.get(f'/api/chefs/{self.hidden.slug}/').status_code, 200)

    def test_reviews_are_published_only(self):
        data = self.client.get(f'/api/chefs/{self.chef.slug}/reviews/').json()
        self.assertEqual({r['customer_name'] for r in data['results']}, {'Grace', 'Brian'})
        data = self.client.get('/api/reviews/?min_rating=4').json()
        self.assertEqual([r['customer_name'] for r in data['results']], ['Grace'])

    def test_packages_and_stats(self):
        data = self.client.get('/api/packages/').json()
        self.assertEqual([p['name'] for p in data['results']], ['Dinner for 6'])
        self.assertEqual(data['results'][0]['chef']['slug'], self.chef.slug)
        self.assertTrue(data['results'][0]['chef']['photo'].startswith('http://testserver/'))
        stats = self.client.get('/api/stats/').json()
        self.assertEqual((stats['chefs'], stats['packages']), (1, 1))

    def test_services_and_cities(self):
        self.assertEqual(len(self.client.get('/api/services/').json()), ServiceCategory.objects.count())
        self.assertEqual(len(self.client.get('/api/cities/').json()), City.objects.count())

    @override_settings(SOCIAL_LINKS={'instagram': 'https://instagram.com/simplychefke', 'tiktok': ''})
    def test_site_details(self):
        data = self.client.get('/api/site/').json()
        self.assertEqual(data['whatsapp_display'], settings.WHATSAPP_DISPLAY)
        self.assertEqual(data['social_links'], [{'icon': 'instagram', 'url': 'https://instagram.com/simplychefke'}])

    def test_api_is_read_only(self):
        self.assertEqual(self.client.post('/api/chefs/', {'name': 'X'}).status_code, 405)
        self.assertEqual(self.client.delete(f'/api/chefs/{self.chef.slug}/').status_code, 405)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class FormApiTests(TestCase):
    """The forms API the Next.js frontend posts to (api_forms.py)."""

    def setUp(self):
        self.chef = make_chef()
        self.package = ChefPackage.objects.create(chef=self.chef, name='Dinner for 6', description='3 courses', price=9000)

    def booking_data(self, **kwargs):
        return {
            'full_name': 'Grace Muthoni', 'phone': '0712345678', 'event_date': datetime.date.today() + datetime.timedelta(days=3),
            'time_slot': 'lunch', 'guests': 4, 'location': 'Kileleshwa', **kwargs,
        }

    def test_get_describes_the_form_like_the_template(self):
        fields = {f['name']: f for f in self.client.get('/api/match-requests/').json()['fields']}
        self.assertEqual(list(fields)[:3], ['full_name', 'phone', 'email'])
        self.assertEqual(fields['full_name']['label'], 'Full name')
        self.assertEqual(fields['phone']['type'], 'tel')
        self.assertEqual(fields['phone']['attrs']['placeholder'], '07XX XXX XXX')
        self.assertEqual(fields['cuisine']['choices'][0], ['', 'Let the chef decide'])
        self.assertEqual(fields['event_date']['attrs']['min'], datetime.date.today().isoformat())
        self.assertEqual(fields['notes']['type'], 'textarea')
        self.assertTrue(fields['phone']['required'])
        self.assertFalse(fields['email']['required'])

    def test_errors_and_success(self):
        resp = self.client.post('/api/contact/', {'name': 'Grace', 'email': 'nope', 'subject': 'general', 'message': 'Hi'})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(list(resp.json()['errors']), ['email'])
        resp = self.client.post('/api/contact/', {'name': 'Grace', 'email': 'grace@example.com', 'subject': 'general', 'message': 'Hi'})
        self.assertEqual(resp.json(), {'message': "Message sent! We'll reply as soon as we can."})
        self.assertTrue(ContactMessage.objects.exists())
        self.assertEqual(self.client.post('/api/subscribe/', {'email': 'A@B.com'}).status_code, 200)
        self.assertEqual(Subscriber.objects.get().email, 'a@b.com')

    def test_posts_need_the_csrf_token_even_when_logged_out(self):
        client = Client(enforce_csrf_checks=True)
        data = {'name': 'Grace', 'email': 'grace@example.com', 'subject': 'general', 'message': 'Hi'}
        self.assertEqual(client.post('/api/contact/', data).status_code, 403)
        client.get('/api/auth/me/')
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post('/api/contact/', data, HTTP_X_CSRFTOKEN=token).status_code, 200)

    @override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
    def test_forwarded_address_passes_the_csrf_origin_check(self):
        client = Client(enforce_csrf_checks=True)
        client.get('/api/auth/me/')
        token = client.cookies['csrftoken'].value
        resp = client.post('/api/subscribe/', {'email': 'a@b.com'}, HTTP_X_CSRFTOKEN=token,
                           HTTP_ORIGIN='http://localhost:3000', HTTP_X_FORWARDED_HOST='localhost:3000')
        self.assertEqual(resp.status_code, 200)
        resp = client.post('/api/subscribe/', {'email': 'a@b.com'}, HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN='http://evil.example')
        self.assertEqual(resp.status_code, 403)

    def test_chef_application_with_uploads(self):
        self.assertEqual(self.client.post('/api/chef-applications/', application_data()).status_code, 200)
        self.assertEqual(ChefApplication.objects.get().dish_photos.count(), 3)
        resp = self.client.post('/api/chef-applications/', application_data(dish_photos=[]))
        self.assertIn('dish_photos', resp.json()['errors'])

    def test_booking_form_and_guest_access_to_the_booking(self):
        fields = {f['name']: f for f in self.client.get(f'/api/chefs/{self.chef.slug}/booking/?package={self.package.pk}').json()['fields']}
        self.assertEqual(fields['package']['value'], str(self.package.pk))
        self.assertEqual(fields['package']['choices'], [['', 'Not sure yet / custom request'], [str(self.package.pk), str(self.package)]])

        resp = self.client.post(f'/api/chefs/{self.chef.slug}/booking/', self.booking_data())
        booking = BookingRequest.objects.get()
        self.assertEqual(resp.json(), {'redirect': reverse('booking_confirmation', args=[booking.pk])})
        self.assertTrue(mail.outbox)  # the booking alert

        data = self.client.get(f'/api/bookings/{booking.pk}/').json()  # booked in this browser
        self.assertEqual((data['status'], data['is_owner'], data['phone']), ('new', False, '+254712345678'))
        self.assertEqual(Client().get(f'/api/bookings/{booking.pk}/').status_code, 404)
        key = booking.customer_url().split('key=')[1]
        self.assertEqual(Client().get(f'/api/bookings/{booking.pk}/?key={key}').status_code, 200)

    def test_booking_errors_and_paused_chef(self):
        resp = self.client.post(f'/api/chefs/{self.chef.slug}/booking/', self.booking_data(event_date='2020-01-01'))
        self.assertEqual(resp.json()['errors']['event_date'], ['Please choose a date from today onwards.'])
        Chef.objects.filter(pk=self.chef.pk).update(is_accepting_bookings=False)
        resp = self.client.post(f'/api/chefs/{self.chef.slug}/booking/', self.booking_data())
        self.assertEqual(resp.json()['errors']['__all__'], [f'{self.chef.name} is not taking new bookings right now.'])

    def test_logged_in_customer_gets_their_details_and_review_prompt(self):
        user = User.objects.create_user('grace@example.com', 'grace@example.com', 'pw', first_name='Grace', last_name='M')
        done = make_booking(self.chef, customer=user, status=BookingRequest.Status.COMPLETED, phone='+254700000001')
        self.client.force_login(user)
        data = self.client.get(f'/api/chefs/{self.chef.slug}/booking/').json()
        fields = {f['name']: f['value'] for f in data['fields']}
        self.assertEqual((fields['full_name'], fields['phone']), ('Grace M', '+254700000001'))
        self.assertEqual(data['booking_to_review']['id'], done.pk)
        self.assertTrue(data['logged_in'])
        self.assertFalse(data['is_own_profile'])

    def test_hidden_chef_can_see_but_not_book_their_own_form(self):
        self.chef.user = User.objects.create_user('wanjiru@example.com')
        self.chef.is_active = False
        self.chef.save()
        self.client.force_login(self.chef.user)
        self.assertTrue(self.client.get(f'/api/chefs/{self.chef.slug}/booking/').json()['is_own_profile'])
        self.assertEqual(self.client.post(f'/api/chefs/{self.chef.slug}/booking/', self.booking_data()).status_code, 404)
        self.assertEqual(Client().get(f'/api/chefs/{self.chef.slug}/booking/').status_code, 404)

    def test_payment_and_review(self):
        user = User.objects.create_user('grace@example.com')
        booking = make_booking(self.chef, customer=user, status=BookingRequest.Status.CONFIRMED, price=9000)
        self.client.force_login(user)
        resp = self.client.post(f'/api/bookings/{booking.pk}/pay/', {'mpesa_code': 'sjk4h7l2qp'})
        self.assertEqual(resp.json()['redirect'], reverse('booking_confirmation', args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual((booking.mpesa_code, booking.payment_status), ('SJK4H7L2QP', 'submitted'))

        resp = self.client.post(f'/api/bookings/{booking.pk}/review/', {'customer_name': 'Grace', 'rating': 5, 'comment': 'Yum'})
        self.assertEqual(resp.json()['errors']['__all__'], ['You can review your chef once the booking is completed.'])
        booking.status = BookingRequest.Status.COMPLETED
        booking.save()
        fields = {f['name']: f for f in self.client.get(f'/api/bookings/{booking.pk}/review/').json()['fields']}
        self.assertEqual(fields['customer_name']['value'], 'Grace')
        self.assertEqual(fields['rating']['choices'][0], ['5', '5 stars'])
        self.client.post(f'/api/bookings/{booking.pk}/review/', {'customer_name': 'Grace', 'rating': 5, 'comment': 'Yum'})
        self.assertEqual(self.client.get(f'/api/bookings/{booking.pk}/').json()['review_status'], 'pending')

    def test_signup_login_logout(self):
        resp = self.client.post('/api/auth/signup/', {
            'full_name': 'Grace Muthoni', 'email': 'Grace@Example.com', 'password1': 'sukuma-wiki-42', 'password2': 'sukuma-wiki-42',
            'next': '/chefs/x/',
        })
        self.assertEqual(resp.json()['redirect'], '/chefs/x/')
        self.assertEqual(self.client.get('/api/auth/me/').json()['user']['first_name'], 'Grace')
        self.assertEqual(self.client.post('/api/auth/logout/').json(), {'redirect': '/'})
        self.assertIsNone(self.client.get('/api/auth/me/').json()['user'])

        resp = self.client.post('/api/auth/login/', {'username': 'grace@example.com', 'password': 'wrong'})
        self.assertIn('__all__', resp.json()['errors'])
        resp = self.client.post('/api/auth/login/?next=https://evil.example/', {'username': 'grace@example.com', 'password': 'sukuma-wiki-42'})
        self.assertEqual(resp.json()['redirect'], reverse('account'))
        self.assertEqual(self.client.get('/api/auth/login/').json()['redirect'], reverse('account'))

    def test_account_and_cancel(self):
        self.assertEqual(self.client.get('/api/account/').status_code, 403)
        user = User.objects.create_user('grace@example.com')
        booking = make_booking(self.chef, customer=user)
        confirmed = make_booking(self.chef, customer=user, status=BookingRequest.Status.CONFIRMED)
        self.client.force_login(user)
        self.assertEqual(len(self.client.get('/api/account/').json()['bookings']), 2)
        self.assertEqual(self.client.post(f'/api/account/bookings/{booking.pk}/cancel/').status_code, 200)
        self.assertEqual(self.client.post(f'/api/account/bookings/{confirmed.pk}/cancel/').status_code, 400)
        self.assertEqual(
            sorted(BookingRequest.objects.values_list('status', flat=True)), ['cancelled', 'confirmed'],
        )

    @override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
    def test_password_reset_link_opens_the_frontend(self):
        user = User.objects.create_user('grace@example.com', 'grace@example.com', 'old-password-1')
        resp = self.client.post('/api/auth/password-reset/', {'email': 'grace@example.com'}, HTTP_X_FORWARDED_HOST='localhost:3000')
        self.assertEqual(resp.json(), {'redirect': reverse('password_reset_done')})
        self.assertIn('http://localhost:3000/account/password-reset/', mail.outbox[0].body)

        path = set_password_path(user).removeprefix('/account/password-reset/')
        data = self.client.get(f'/api/auth/password-reset/{path}').json()
        self.assertEqual((data['validlink'], data['username']), (True, 'grace@example.com'))
        resp = self.client.post(f'/api/auth/password-reset/{path}', {'new_password1': 'ugali-sukuma-7', 'new_password2': 'ugali-sukuma-7'})
        self.assertEqual(resp.json(), {'redirect': reverse('password_reset_complete')})
        self.assertFalse(self.client.get(f'/api/auth/password-reset/{path}').json()['validlink'])
        user.refresh_from_db()
        self.assertTrue(user.check_password('ugali-sukuma-7'))


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class ChefApiTests(TestCase):
    """The chef dashboard API (api_chef.py)."""

    def setUp(self):
        self.chef = make_chef(is_verified=True)
        self.user = invite_chef(self.chef)
        self.client.force_login(self.user)
        mail.outbox.clear()

    def test_chefs_only(self):
        self.client.force_login(User.objects.create_user('grace@example.com'))
        self.assertEqual(self.client.get('/api/chef/').status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get('/api/chef/profile/').status_code, 403)

    def test_dashboard_lists_own_bookings_and_hides_phone_until_confirmed(self):
        new = make_booking(self.chef)
        make_booking(self.chef, status=BookingRequest.Status.CONFIRMED, phone='+254700000001')
        make_booking(make_chef('Chef Otieno', 'otieno@example.com'), full_name='Other Customer')
        new.messages.create(from_chef=False, body='Hello')
        data = self.client.get('/api/chef/').json()
        self.assertEqual(data['chef']['name'], 'Chef Wanjiru')
        self.assertEqual(data['total'], 2)
        self.assertEqual(sorted(b['phone'] for b in data['bookings']), ['', '+254700000001'])
        self.assertEqual(self.client.get('/api/chef/?status=new').json()['bookings'][0]['message_count'], 1)

    def test_confirm_with_price_then_message_customer(self):
        booking = make_booking(self.chef)
        self.assertEqual(self.client.get(f'/api/chef/bookings/{booking.pk}/').json()['booking']['next_statuses'], ['confirmed', 'cancelled'])
        resp = self.client.post(f'/api/chef/bookings/{booking.pk}/status/', {'status': 'confirmed'})
        self.assertEqual(resp.json()['errors']['__all__'], ['Enter the price the customer will pay before confirming.'])
        resp = self.client.post(f'/api/chef/bookings/{booking.pk}/status/', {'status': 'confirmed', 'price': 6000})
        self.assertEqual(resp.json(), {'message': 'Booking for Grace Muthoni marked confirmed.'})
        self.assertIn('grace@example.com', [m.to[0] for m in mail.outbox])

        resp = self.client.post(f'/api/chef/bookings/{booking.pk}/', {'body': 'Any allergies?'})
        self.assertEqual(resp.json()['redirect'], f'/chef/bookings/{booking.pk}/#messages')
        self.assertEqual(self.client.get(f'/api/chef/bookings/{booking.pk}/').json()['messages'][0]['body'], 'Any allergies?')

    def test_other_chefs_bookings_are_not_found(self):
        other = make_booking(make_chef('Chef Otieno', 'otieno@example.com'))
        self.assertEqual(self.client.get(f'/api/chef/bookings/{other.pk}/').status_code, 404)
        self.assertEqual(self.client.post(f'/api/chef/bookings/{other.pk}/status/', {'status': 'cancelled'}).status_code, 404)

    def test_availability(self):
        make_booking(self.chef, status=BookingRequest.Status.CONFIRMED, event_date=in_days(3))
        resp = self.client.post('/api/chef/availability/', {'start_date': in_days(2), 'end_date': in_days(4), 'note': 'Wedding'})
        self.assertIn('1 confirmed booking', resp.json()['warning'])
        data = self.client.get('/api/chef/availability/').json()
        self.assertEqual([t['note'] for t in data['time_off']], ['Wedding'])
        self.assertEqual(len(data['upcoming']), 1)

        self.client.post(f"/api/chef/availability/{data['time_off'][0]['id']}/delete/")
        self.assertFalse(self.chef.time_off.exists())
        self.client.post('/api/chef/availability/accepting/', {'accepting': '0'})
        self.chef.refresh_from_db()
        self.assertFalse(self.chef.is_accepting_bookings)

    def test_profile_and_packages(self):
        data = self.client.get('/api/chef/profile/').json()
        fields = {f['name']: f for f in data['fields']}
        self.assertEqual(fields['services']['type'], 'checkboxes')
        self.assertEqual((fields['photo']['type'], fields['photo']['url'], fields['photo']['clearable']), ('file', '', True))
        management = {f['name']: f['value'] for f in data['packages']['management']}
        self.assertEqual(management['packages-TOTAL_FORMS'], '1')
        self.assertEqual(data['packages']['forms'][0][0]['name'], 'packages-0-name')

        profile = {
            'headline': 'New headline', 'bio': 'New bio', 'services': [ServiceCategory.objects.first().pk], 'cuisine': 'kenyan',
            'city': self.chef.city_id, 'area': 'Kilimani', 'years_experience': 5, 'starting_price': 5000,
            'price_unit': 'per event', 'phone': '0712345678', 'packages-TOTAL_FORMS': 1, 'packages-INITIAL_FORMS': 0,
        }
        resp = self.client.post('/api/chef/profile/', {**profile, 'headline': '', 'packages-0-name': 'Family lunch'})
        self.assertEqual(set(resp.json()['errors']), {'headline', 'packages-0-description', 'packages-0-price', 'packages-0-price_unit'})
        resp = self.client.post('/api/chef/profile/', {
            **profile, 'packages-0-name': 'Family lunch', 'packages-0-description': 'For 6', 'packages-0-price': 5000,
            'packages-0-price_unit': 'per event', 'packages-0-is_active': 'on',
        })
        self.assertEqual(resp.json()['redirect'], '/chef/profile/')
        self.assertEqual(self.chef.packages.get().name, 'Family lunch')

    def test_photos_and_documents(self):
        resp = self.client.post('/api/chef/photos/', {'photos-TOTAL_FORMS': 0, 'photos-INITIAL_FORMS': 0, 'new_photos': [dish_photo('a.png'), dish_photo('b.png')]})
        self.assertEqual(resp.json()['message'], '2 photos added.')
        data = self.client.get('/api/chef/photos/').json()
        self.assertEqual((len(data['images']), data['max_photos']), (2, 12))
        self.assertEqual(data['photos']['forms'][0][0]['name'], 'photos-0-caption')

        self.assertIn('__all__', self.client.post('/api/chef/documents/', {}).json()['errors'])
        resp = self.client.post('/api/chef/documents/', {'national_id': SimpleUploadedFile('id.pdf', b'%PDF')})
        self.assertEqual(resp.json()['redirect'], '/chef/documents/')
        fields = {f['name']: f for f in self.client.get('/api/chef/documents/').json()['fields']}
        self.assertTrue(fields['national_id']['url'].startswith('/media/chefs/documents/ids/'))
        self.chef.refresh_from_db()
        self.assertFalse(self.chef.is_verified)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class TeamApiTests(TestCase):
    """The team API (api_team.py)."""

    def setUp(self):
        self.client.force_login(User.objects.create_user('team@example.com', 'team@example.com', 'pw', is_staff=True, first_name='Wanjiku'))

    def test_staff_only(self):
        self.client.force_login(User.objects.create_user('grace@example.com'))
        self.assertEqual(self.client.get('/api/team/').status_code, 403)
        self.assertEqual(self.client.post('/api/team/inbox/1/replied/').status_code, 403)

    def test_home_and_lists(self):
        make_application()
        booking = make_booking(make_chef(), status=BookingRequest.Status.CONFIRMED, event_date=in_days(2), price=6000)
        data = self.client.get('/api/team/').json()
        self.assertEqual((data['first_name'], data['waiting']['applications']), ('Wanjiku', 1))
        self.assertEqual(data['upcoming'][0]['payment_reference'], booking.payment_reference)
        self.assertEqual(len(self.client.get('/api/team/applications/').json()['items']), 1)
        self.assertEqual(self.client.get('/api/team/bookings/').json()['items'], [])  # new ones by default
        self.assertEqual(len(self.client.get('/api/team/bookings/?status=').json()['items']), 1)
        self.assertEqual(self.client.get('/api/team/chefs/?show=live').json()['show'], 'live')

    def test_approve_then_put_live(self):
        application = make_application()
        data = self.client.get(f'/api/team/applications/{application.pk}/').json()
        self.assertTrue(data['application']['national_id'].startswith('/media/'))
        self.assertEqual(data['approve_fields'][0]['name'], 'message')
        self.assertEqual(self.client.post(f'/api/team/applications/{application.pk}/reject/', {'reason': ''}).status_code, 400)
        resp = self.client.post(f'/api/team/applications/{application.pk}/approve/', {'message': 'Karibu!'})
        self.assertEqual(resp.json(), {'message': 'Amina Hassan approved and emailed a welcome with their login.'})
        chef = self.client.get(f'/api/team/applications/{application.pk}/').json()['application']['chef']
        self.assertEqual((chef['is_active'], chef['has_login']), (False, True))

        self.client.post(f"/api/team/chefs/{chef['id']}/live/", {'on': '1'})
        self.assertTrue(Chef.objects.get().is_active)
        self.assertEqual(self.client.post(f"/api/team/chefs/{chef['id']}/nonsense/", {'on': '1'}).status_code, 404)

    def test_booking_status_payment_and_notes(self):
        booking = make_booking(make_chef())
        self.client.post(f'/api/team/bookings/{booking.pk}/status/', {'status': 'confirmed', 'price': 6000})
        booking.refresh_from_db()
        self.assertEqual((booking.status, booking.price), ('confirmed', 6000))
        resp = self.client.post(f'/api/team/bookings/{booking.pk}/payment/', {'payment_status': 'refunded'})
        self.assertEqual(resp.status_code, 400)
        self.client.post(f'/api/team/bookings/{booking.pk}/payment/', {'payment_status': 'paid'})
        booking.refresh_from_db()
        self.assertEqual(booking.payment_status, 'paid')

        resp = self.client.post(f'/api/team/bookings/{booking.pk}/', {'price': 6500, 'team_notes': 'Moved to 7 PM'})
        self.assertEqual(resp.json(), {'message': 'Booking saved.', 'redirect': f'/team/bookings/{booking.pk}/'})
        data = self.client.get(f'/api/team/bookings/{booking.pk}/').json()
        self.assertEqual((data['booking']['team_notes'], data['booking']['phone'], data['clash']), ('Moved to 7 PM', '+254700000000', False))

    def test_reviews_requests_and_inbox(self):
        chef = make_chef()
        review = Review.objects.create(chef=chef, customer_name='Grace', rating=5, comment='Lovely')
        match = ChefMatchRequest.objects.create(
            full_name='Jane', phone='+254712345678', occasion='party', guests='7-15',
            event_date=datetime.date.today(), time_slot='dinner', location='Kilimani',
        )
        msg = ContactMessage.objects.create(name='Brian', email='brian@example.com', subject='events', message='Hello')
        self.assertEqual(self.client.get('/api/team/reviews/').json()['items'][0]['comment'], 'Lovely')
        self.client.post(f'/api/team/reviews/{review.pk}/status/', {'status': 'published'})
        self.assertEqual(self.client.post(f'/api/team/reviews/{review.pk}/status/', {'status': 'published'}).json(), {})
        self.assertEqual(self.client.get('/api/team/requests/').json()['items'][0]['occasion_display'], 'Birthday / Party')
        self.client.post(f'/api/team/requests/{match.pk}/status/', {'status': 'matched'})
        self.assertEqual(len(self.client.get('/api/team/inbox/').json()['items']), 1)
        self.client.post(f'/api/team/inbox/{msg.pk}/replied/')
        review.refresh_from_db(), match.refresh_from_db(), msg.refresh_from_db()
        self.assertEqual((review.status, match.status, msg.is_handled), ('published', 'matched', True))
        self.assertEqual(self.client.get('/api/team/inbox/?show=all').json()['show_all'], True)

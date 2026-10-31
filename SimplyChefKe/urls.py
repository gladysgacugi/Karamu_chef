"""
URL configuration for Config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from . import api, api_chef, api_forms, api_team, views
from .forms import StyledPasswordResetForm, StyledSetPasswordForm

api_router = DefaultRouter()
api_router.register('services', api.ServiceViewSet)
api_router.register('cities', api.CityViewSet)
api_router.register('chefs', api.ChefViewSet, basename='chef')
api_router.register('packages', api.PackageViewSet, basename='package')
api_router.register('reviews', api.ReviewViewSet, basename='review')

# Forms and accounts API for the Next.js frontend
api_form_urls = [
    path('chef-applications/', api_forms.ChefApplicationEndpoint.as_view(), name='chef_application'),
    path('match-requests/', api_forms.MatchRequestEndpoint.as_view(), name='match_request'),
    path('contact/', api_forms.ContactEndpoint.as_view(), name='contact'),
    path('subscribe/', api_forms.SubscribeEndpoint.as_view(), name='subscribe'),
    path('chefs/<slug:slug>/booking/', api_forms.BookingEndpoint.as_view(), name='chef_booking'),
    path('bookings/<int:pk>/', api_forms.booking, name='booking'),
    path('bookings/<int:pk>/pay/', api_forms.PaymentEndpoint.as_view(), name='booking_pay'),
    path('bookings/<int:pk>/review/', api_forms.ReviewEndpoint.as_view(), name='booking_review'),
    path('bookings/<int:pk>/messages/', api_forms.MessageEndpoint.as_view(), name='booking_message'),
    path('auth/me/', api_forms.me, name='me'),
    path('auth/login/', api_forms.LoginEndpoint.as_view(), name='login'),
    path('auth/logout/', api_forms.logout_view, name='logout'),
    path('auth/signup/', api_forms.SignUpEndpoint.as_view(), name='signup'),
    path('auth/password-reset/', api_forms.PasswordResetEndpoint.as_view(), name='password_reset'),
    path('auth/password-reset/<uidb64>/<token>/', api_forms.SetPasswordEndpoint.as_view(), name='set_password'),
    path('account/', api_forms.account, name='account'),
    path('account/bookings/<int:pk>/cancel/', api_forms.cancel_booking, name='cancel_booking'),
]

# Chef dashboard API
api_chef_urls = [
    path('', api_chef.DashboardEndpoint.as_view(), name='dashboard'),
    path('bookings/<int:pk>/', api_chef.BookingEndpoint.as_view(), name='booking'),
    path('bookings/<int:pk>/status/', api_chef.booking_status, name='booking_status'),
    path('availability/', api_chef.AvailabilityEndpoint.as_view(), name='availability'),
    path('availability/accepting/', api_chef.accepting, name='accepting'),
    path('availability/<int:pk>/delete/', api_chef.delete_time_off, name='delete_time_off'),
    path('profile/', api_chef.ProfileEndpoint.as_view(), name='profile'),
    path('photos/', api_chef.PhotosEndpoint.as_view(), name='photos'),
    path('documents/', api_chef.DocumentsEndpoint.as_view(), name='documents'),
]

# Team API
api_team_urls = [
    path('', api_team.home, name='home'),
    path('waiting/', api_team.waiting, name='waiting'),
    path('applications/', api_team.applications, name='applications'),
    path('applications/<int:pk>/', api_team.application, name='application'),
    path('applications/<int:pk>/approve/', api_team.approve_application, name='approve_application'),
    path('applications/<int:pk>/reject/', api_team.reject_application, name='reject_application'),
    path('chefs/', api_team.chefs, name='chefs'),
    path('chefs/<int:pk>/<slug:switch>/', api_team.chef_switch, name='chef_switch'),
    path('bookings/', api_team.bookings, name='bookings'),
    path('bookings/<int:pk>/', api_team.BookingEndpoint.as_view(), name='booking'),
    path('bookings/<int:pk>/status/', api_team.booking_status, name='booking_status'),
    path('bookings/<int:pk>/payment/', api_team.booking_payment, name='booking_payment'),
    path('reviews/', api_team.reviews, name='reviews'),
    path('reviews/<int:pk>/status/', api_team.review_status, name='review_status'),
    path('requests/', api_team.requests, name='requests'),
    path('requests/<int:pk>/status/', api_team.request_status, name='request_status'),
    path('inbox/', api_team.inbox, name='inbox'),
    path('inbox/<int:pk>/replied/', api_team.message_replied, name='message_replied'),
]

urlpatterns = [
    # Public API for the Next.js frontend
    path('api/stats/', api.stats, name='api_stats'),
    path('api/site/', api.site, name='api_site'),
    path('api/chef/', include((api_chef_urls, 'api_chef'))),
    path('api/team/', include((api_team_urls, 'api_team'))),
    path('api/', include((api_form_urls, 'api_forms'))),
    path('api/', include((api_router.urls, 'api'))),

    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('become-a-chef/', views.become_chef, name='become_chef'),
    path('request-a-chef/', views.request_chef, name='request_chef'),
    path('contact/', views.contact, name='contact'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('privacy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),
    path('marketplace/', views.marketplace, name='marketplace'),
    path('chefs/<slug:slug>/', views.chef_detail, name='chef_detail'),
    path('chefs/<slug:slug>/book/', views.book_chef, name='book_chef'),
    path('bookings/<int:pk>/', views.booking_confirmation, name='booking_confirmation'),
    path('bookings/<int:pk>/pay/', views.booking_checkout, name='booking_checkout'),
    path('bookings/<int:pk>/review/', views.booking_review, name='booking_review'),

    # Customer accounts
    path('account/', views.account, name='account'),
    path('account/signup/', views.signup, name='signup'),
    path('account/login/', views.LoginView.as_view(), name='login'),
    path('account/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('account/bookings/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('account/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        form_class=StyledPasswordResetForm,
    ), name='password_reset'),
    path('account/password-reset/sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
    ), name='password_reset_done'),
    path('account/password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        form_class=StyledSetPasswordForm,
    ), name='password_reset_confirm'),
    path('account/password-reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Chef dashboard
    path('chef/', views.chef_dashboard, name='chef_dashboard'),
    path('chef/profile/', views.chef_profile_edit, name='chef_profile_edit'),
    path('chef/photos/', views.chef_photos, name='chef_photos'),
    path('chef/documents/', views.chef_documents, name='chef_documents'),
    path('chef/bookings/<int:pk>/', views.chef_booking, name='chef_booking'),
    path('chef/availability/', views.chef_availability, name='chef_availability'),
    path('chef/availability/<int:pk>/delete/', views.chef_time_off_delete, name='chef_time_off_delete'),
    path('chef/bookings/<int:pk>/status/', views.update_booking_status, name='update_booking_status'),

    # Team (phone-friendly admin)
    path('team/', views.team_home, name='team_home'),
    path('team/applications/', views.team_applications, name='team_applications'),
    path('team/applications/<int:pk>/', views.team_application, name='team_application'),
    path('team/applications/<int:pk>/approve/', views.team_approve_application, name='team_approve_application'),
    path('team/applications/<int:pk>/reject/', views.team_reject_application, name='team_reject_application'),
    path('team/chefs/', views.team_chefs, name='team_chefs'),
    path('team/chefs/<int:pk>/live/', views.team_chef_live, name='team_chef_live'),
    path('team/chefs/<int:pk>/featured/', views.team_chef_featured, name='team_chef_featured'),
    path('team/chefs/<int:pk>/verified/', views.team_chef_verified, name='team_chef_verified'),
    path('team/bookings/', views.team_bookings, name='team_bookings'),
    path('team/bookings/<int:pk>/', views.team_booking, name='team_booking'),
    path('team/bookings/<int:pk>/status/', views.team_booking_status, name='team_booking_status'),
    path('team/bookings/<int:pk>/payment/', views.team_booking_payment, name='team_booking_payment'),
    path('team/reviews/', views.team_reviews, name='team_reviews'),
    path('team/reviews/<int:pk>/status/', views.team_review_status, name='team_review_status'),
    path('team/requests/', views.team_requests, name='team_requests'),
    path('team/requests/<int:pk>/status/', views.team_request_status, name='team_request_status'),
    path('team/inbox/', views.team_inbox, name='team_inbox'),
    path('team/inbox/<int:pk>/replied/', views.team_message_replied, name='team_message_replied'),

    # Removes the service worker of the old installable app from phones that installed it
    path('sw.js', views.service_worker, name='service_worker'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

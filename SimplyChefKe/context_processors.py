from django.conf import settings

from .models import ServiceCategory


def site(request):
    return {
        'whatsapp_url': settings.WHATSAPP_URL,
        'whatsapp_display': settings.WHATSAPP_DISPLAY,
        # Section links like #about only work on the homepage; elsewhere they need to point back to "/"
        'nav_prefix': '' if request.path == '/' else '/',
        'footer_services': ServiceCategory.objects.all(),
        # (Font Awesome brand icon, url) for each social page that has been set up
        'social_links': [(icon, url) for icon, url in settings.SOCIAL_LINKS.items() if url],
    }

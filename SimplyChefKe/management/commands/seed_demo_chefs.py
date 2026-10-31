from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from SimplyChefKe.models import Chef, ChefPackage, City, Review, ServiceCategory

DEMO_EMAIL_DOMAIN = '@demo.simplychefke.com'

# name, headline, cuisine, city, area, years, photo, services, (starting price, unit), packages, reviews
DEMO_CHEFS = [
    ('Chef Wanjiru', 'Kenyan home classics, just like mum makes', 'kenyan', 'nairobi', 'Kilimani', 9, '1.jpg',
     ['private-chefs', 'meal-prep', 'home-cooked-meals'], (4500, 'per event'),
     [('Sunday Family Lunch', 'Mukimo, beef stew, chapati, sukuma and fruit salad for up to 6 guests.', 4500, 'per event'),
      ('Weekly Meal Prep', '5 balanced dinners for a family of 4, packed and labelled.', 6500, 'per week')],
     [('Grace M.', 5, 'The mukimo tasted exactly like home. My kids finished everything!'),
      ('Peter N.', 5, 'Punctual, clean and the chapatis were perfect.')]),
    ('Chef Otieno', 'Grill master - nyama choma for every celebration', 'grills', 'nairobi', 'Westlands', 12, '2.jpg',
     ['nyama-choma-grills', 'event-catering', 'private-chefs'], (6000, 'per event'),
     [('Nyama Choma Party', 'Goat ribs and beef roasted on site, kachumbari and ugali. Up to 15 guests.', 15000, 'per event'),
      ('Backyard BBQ for 6', 'Chicken, beef skewers and sausages with sides.', 6000, 'per event')],
     [('Brian K.', 5, 'Best nyama choma at my birthday - everyone asked for his number.')]),
    ('Chef Amina', 'Swahili coastal cuisine from Mombasa', 'coastal', 'mombasa', 'Nyali', 10, '3.jpg',
     ['private-chefs', 'home-cooked-meals', 'cooking-classes'], (5000, 'per event'),
     [('Swahili Feast', 'Biryani, pilau, samaki wa kupaka, viazi karai and mahamri for 8.', 9000, 'per event'),
      ('Pilau & Biryani Class', 'Hands-on 3-hour class for up to 4 people.', 3500, 'per class')],
     [('Fatma S.', 5, 'Her biryani is unreal. The class was so much fun too.'),
      ('David O.', 4, 'Great food, arrived a little late but worth it.')]),
    ('Chef Kiprono', 'Events, corporate catering and meal prep', 'continental', 'nakuru', 'Milimani', 7, '4.jpg',
     ['event-catering', 'meal-prep'], (800, 'per guest'),
     [('Office Lunch Buffet', 'Two mains, sides, salad and dessert. Minimum 20 guests.', 950, 'per guest'),
      ('Healthy Meal Prep', '10 portion-controlled lunches for the week.', 4500, 'per week')],
     []),
]


class Command(BaseCommand):
    help = 'Adds demo chefs, packages and reviews for development. Use --clear to remove them. Do not use in production.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete the demo chefs instead of creating them.')

    def handle(self, *args, clear=False, **options):
        demo = Chef.objects.filter(email__endswith=DEMO_EMAIL_DOMAIN)
        if clear:
            count = demo.count()
            demo.delete()
            self.stdout.write(self.style.SUCCESS(f'Removed {count} demo chef(s).'))
            return

        photo_dir = Path(settings.BASE_DIR) / 'static' / 'img' / 'chefs'
        created = 0
        for (name, headline, cuisine, city, area, years, photo, services, (price, unit),
             packages, reviews) in DEMO_CHEFS:
            email = name.split()[-1].lower() + DEMO_EMAIL_DOMAIN
            if Chef.objects.filter(email=email).exists():
                continue
            chef = Chef(
                name=name, headline=headline, cuisine=cuisine, city=City.objects.get(slug=city), area=area,
                years_experience=years, starting_price=price, price_unit=unit,
                bio=f'{name} has been cooking professionally for {years} years. (Demo profile - replace with a real chef.)',
                phone='+254700000000', email=email, is_verified=True, is_featured=True,
            )
            with open(photo_dir / photo, 'rb') as f:
                chef.photo.save(f'demo-{photo}', File(f), save=False)
            chef.save()
            chef.services.set(ServiceCategory.objects.filter(slug__in=services))
            for order, (pkg_name, desc, pkg_price, pkg_unit) in enumerate(packages):
                ChefPackage.objects.create(chef=chef, name=pkg_name, description=desc, price=pkg_price,
                                           price_unit=pkg_unit, order=order)
            for customer, rating, comment in reviews:
                Review.objects.create(chef=chef, customer_name=customer, rating=rating, comment=comment,
                                      status=Review.Status.PUBLISHED)
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created} demo chef(s). Remove them later with --clear.'))

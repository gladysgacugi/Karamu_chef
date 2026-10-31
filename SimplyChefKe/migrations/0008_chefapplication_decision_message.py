from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SimplyChefKe', '0007_chef_documents_booking_messages'),
    ]

    operations = [
        migrations.AddField(
            model_name='chefapplication',
            name='decision_message',
            field=models.TextField(blank=True, help_text='The welcome message or rejection reason we emailed the applicant.'),
        ),
    ]

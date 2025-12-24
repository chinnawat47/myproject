# Generated migration to add audit fields and signup status
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volunteer_app', '0003_activity_status_ideaproposal_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitysignup',
            name='status',
            field=models.CharField(choices=[('requested', 'Requested'), ('confirmed', 'Confirmed'), ('attended', 'Attended'), ('waitlist', 'Waitlist'), ('cancelled', 'Cancelled')], default='requested', max_length=20),
        ),
        migrations.AddField(
            model_name='qrscan',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='qrscan',
            name='user_agent',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name='qrscan',
            name='device_id',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='qrscan',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='qrscan',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='qrscan',
            name='scanned_from_staff',
            field=models.BooleanField(default=False),
        ),
    ]

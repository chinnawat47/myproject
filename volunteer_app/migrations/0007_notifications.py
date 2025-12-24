from django.db import migrations, models
from django.conf import settings


def seed_notification_prefs(apps, schema_editor):
    User = apps.get_model("volunteer_app", "User")
    NotificationPreference = apps.get_model("volunteer_app", "NotificationPreference")
    for user in User.objects.all():
        NotificationPreference.objects.get_or_create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ("volunteer_app", "0006_role_management"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("message", models.TextField()),
                ("category", models.CharField(choices=[("general", "ทั่วไป"), ("idea", "ไอเดีย"), ("activity", "กิจกรรม"), ("hours", "ชั่วโมงจิตอาสา")], default="general", max_length=20)),
                ("target_url", models.CharField(blank=True, max_length=500)),
                ("data", models.JSONField(blank=True, null=True)),
                ("channel", models.CharField(choices=[("in_app", "In-app"), ("email", "Email"), ("both", "In-app + Email")], default="in_app", max_length=10)),
                ("is_read", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("in_app_enabled", models.BooleanField(default=True)),
                ("email_enabled", models.BooleanField(default=True)),
                ("idea_updates", models.BooleanField(default=True)),
                ("activity_reminders", models.BooleanField(default=True)),
                ("hours_updates", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="notification_pref", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(seed_notification_prefs, migrations.RunPython.noop),
    ]


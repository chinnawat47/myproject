# Generated manually for email verification feature

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("volunteer_app", "0007_notifications"),
    ]

    operations = [
        # Add email verification fields to User model
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Create EmailVerification model
        migrations.CreateModel(
            name="EmailVerification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField()),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="email_verifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        # Add database indexes for frequently queried fields
        migrations.AddIndex(
            model_name="activity",
            index=models.Index(fields=["datetime"], name="volunteer_a_act_datetime_idx"),
        ),
        migrations.AddIndex(
            model_name="activity",
            index=models.Index(fields=["status"], name="volunteer_a_act_status_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email"], name="volunteer_a_user_email_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email_verified"], name="volunteer_a_user_email_v_idx"),
        ),
        migrations.AddIndex(
            model_name="qrscan",
            index=models.Index(fields=["scanned_at"], name="volunteer_a_qr_scanned_idx"),
        ),
        migrations.AddIndex(
            model_name="activitysignup",
            index=models.Index(fields=["status"], name="volunteer_a_signup_status_idx"),
        ),
        migrations.AddIndex(
            model_name="emailverification",
            index=models.Index(fields=["token"], name="volunteer_a_email_token_idx"),
        ),
        migrations.AddIndex(
            model_name="emailverification",
            index=models.Index(fields=["expires_at"], name="volunteer_a_email_expires_idx"),
        ),
    ]


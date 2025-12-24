from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("volunteer_app", "0004_add_qr_and_signup_status"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Vote",
        ),
        migrations.CreateModel(
            name="IdeaVote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("voted_at", models.DateTimeField(auto_now_add=True)),
                ("idea", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="volunteer_app.ideaproposal")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="idea_votes", to="volunteer_app.user")),
            ],
            options={
                "unique_together": {("idea", "user")},
            },
        ),
    ]


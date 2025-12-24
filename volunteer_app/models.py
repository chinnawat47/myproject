from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid, secrets
from decimal import Decimal

from .utils import make_qr_token

def activity_image_path(instance, filename):
    return f"activities/{instance.id}/{filename}"

class User(AbstractUser):
    title = models.CharField(max_length=20, blank=True)
    student_id = models.CharField(max_length=20, blank=True)
    faculty = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    roles = models.ManyToManyField("Role", blank=True, related_name="users")

    def total_hours(self):
        return sum(scan.activity.hours_reward for scan in self.qr_scans.all())

    def has_role(self, *codes):
        """Return True if user is assigned to any of the provided role codes."""
        codes = [code.lower() for code in codes if code]
        if not codes:
            return False
        return self.roles.filter(code__in=codes).exists()

    def primary_role(self):
        """Return the highest-priority role assigned to the user (if any)."""
        role = self.roles.order_by("display_order", "name").first()
        return role

    def primary_role_label(self):
        role = self.primary_role()
        return role.name if role else "User"

    def sync_admin_flags_from_roles(self):
        """Keep legacy boolean flags in sync with role assignments."""
        has_staff_like_role = self.has_role("admin", "staff")
        if has_staff_like_role and not self.is_staff:
            self.is_staff = True
        self.is_admin = has_staff_like_role

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"


class Role(models.Model):
    """Role configuration for fine-grained permission & workflow control."""

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=100)
    is_assignable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

# -------------------- ACTIVITY --------------------
class Activity(models.Model):
    TYPE_CHOICES = [
        ("environment", "Environment"),
        ("community", "Community"),
        ("education", "Education"),
        ("health", "Health"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("ongoing", "Ongoing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=TYPE_CHOICES, default="other")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    datetime = models.DateTimeField()
    location = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(default=50)
    hours_reward = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    image = models.ImageField(upload_to=activity_image_path, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_activities")
    created_at = models.DateTimeField(auto_now_add=True)

    def spots_taken(self):
        # count only confirmed/attended signups
        return self.signups.filter(status__in=("confirmed", "attended")).count()

    def is_full(self):
        return self.spots_taken() >= self.capacity

    def qr_token(self):
        # return signed, time-limited token
        if not self.pk:
            return None
        return make_qr_token(self.pk)

    def __str__(self):
        return self.title

# -------------------- SIGNUP & QR --------------------
class ActivitySignup(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="signups")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="signups")
    note = models.TextField(blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("confirmed", "Confirmed"),
        ("attended", "Attended"),
        ("waitlist", "Waitlist"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")

    class Meta:
        unique_together = ("activity", "user")

class QRScan(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="qr_scans")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="qr_scans")
    scanned_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=200)

    # audit fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    device_id = models.CharField(max_length=128, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    scanned_from_staff = models.BooleanField(default=False)

    class Meta:
        unique_together = ("activity", "user")

# -------------------- IDEA --------------------
class IdeaProposal(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    proposer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ideas")
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_votes(self):
        return self.votes.count()


class IdeaVote(models.Model):
    idea = models.ForeignKey(IdeaProposal, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="idea_votes")
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("idea", "user")

# -------------------- NOTIFICATION --------------------
class Notification(models.Model):
    CHANNEL_CHOICES = [
        ("in_app", "In-app"),
        ("email", "Email"),
        ("both", "In-app + Email"),
    ]
    CATEGORY_CHOICES = [
        ("general", "ทั่วไป"),
        ("idea", "ไอเดีย"),
        ("activity", "กิจกรรม"),
        ("hours", "ชั่วโมงจิตอาสา"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    target_url = models.CharField(max_length=500, blank=True)
    data = models.JSONField(blank=True, null=True)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default="in_app")
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_pref")
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    idea_updates = models.BooleanField(default=True)
    activity_reminders = models.BooleanField(default=True)
    hours_updates = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification Preference for {self.user}"

# -------------------- GROUP --------------------
class Group(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=12, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_groups")
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_invite_code(self):
        self.code = secrets.token_urlsafe(8)
        self.save()

    def member_count(self):
        return self.memberships.count()

    def is_member(self, user):
        return self.memberships.filter(user=user).exists()

    def __str__(self):
        return f"{self.name} ({self.code})"

class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"

class GroupPost(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.author} in {self.group.name}"


# -------------------- SIGNALS --------------------
from django.db.models.signals import post_save  # noqa: E402
from django.dispatch import receiver  # noqa: E402


@receiver(post_save, sender=User)
def ensure_notification_pref(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.get_or_create(user=instance)

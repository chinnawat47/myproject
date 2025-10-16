from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

def activity_image_path(instance, filename):
    return f"activities/{instance.id}/{filename}"

class User(AbstractUser):
    # additional profile fields
    title = models.CharField(max_length=20, blank=True)  # คำนำหน้า
    student_id = models.CharField(max_length=20, blank=True)
    faculty = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)

    def total_hours(self):
        # sum hours from confirmed scans
        return sum(scan.activity.hours_reward for scan in self.qr_scans.all())

class Activity(models.Model):
    TYPE_CHOICES = [
        ("environment", "Environment"),
        ("community", "Community"),
        ("education", "Education"),
        ("health", "Health"),
        ("other", "Other"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=TYPE_CHOICES, default="other")
    datetime = models.DateTimeField()
    location = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(default=50)
    hours_reward = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    image = models.ImageField(upload_to=activity_image_path, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_activities")
    created_at = models.DateTimeField(auto_now_add=True)

    def spots_taken(self):
        return self.signups.count()

    def is_full(self):
        return self.spots_taken() >= self.capacity

    def qr_token(self):
        # deterministic token for QR (could be more secure)
        # Use UUID namespace + id to allow offline QR generation
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"activity-{self.id}"))

    def __str__(self):
        return self.title

class ActivitySignup(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="signups")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="signups")
    note = models.TextField(blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("activity", "user")

class QRScan(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="qr_scans")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="qr_scans")
    scanned_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=200)

    class Meta:
        unique_together = ("activity", "user")

class Vote(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="votes")
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("activity", "user")

class IdeaProposal(models.Model):
    proposer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ideas")
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

class Group(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=12, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_groups")
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_invite_code(self):
        # simple random code
        import secrets
        self.code = secrets.token_urlsafe(8)
        self.save()

class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")

class GroupPost(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Activity, ActivitySignup, QRScan, IdeaProposal, IdeaVote,
    Group, GroupMembership, GroupPost, Role, Notification, NotificationPreference
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile", {"fields": ("title", "student_id", "faculty", "department", "year")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "student_id", "faculty", "department", "year")

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "datetime", "location", "capacity", "hours_reward", "spots_taken", "is_full")
    readonly_fields = ("created_at",)
    search_fields = ("title", "description")

@admin.register(ActivitySignup)
class ActivitySignupAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "joined_at")
    search_fields = ("activity__title", "user__username")

@admin.register(QRScan)
class QRScanAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "scanned_at", "token")

@admin.register(IdeaProposal)
class IdeaProposalAdmin(admin.ModelAdmin):
    list_display = ("title", "proposer", "target_hours", "created_at", "reviewed")
    list_filter = ("reviewed",)

@admin.register(IdeaVote)
class IdeaVoteAdmin(admin.ModelAdmin):
    list_display = ("idea", "user", "voted_at")

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_by", "created_at")

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "user", "joined_at")

@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = ("group", "author", "created_at")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "display_order", "is_assignable")
    list_editable = ("display_order", "is_assignable")
    search_fields = ("name", "code")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "channel", "is_read", "created_at")
    list_filter = ("category", "channel", "is_read")
    search_fields = ("title", "message", "user__username")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "in_app_enabled", "email_enabled", "idea_updates", "activity_reminders", "hours_updates")
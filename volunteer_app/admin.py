from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Activity, ActivitySignup, QRScan, Vote, IdeaProposal, Group, GroupMembership, GroupPost

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

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "voted_at")

@admin.register(IdeaProposal)
class IdeaProposalAdmin(admin.ModelAdmin):
    list_display = ("title", "proposer", "target_hours", "created_at", "reviewed")
    list_filter = ("reviewed",)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_by", "created_at")

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "user", "joined_at")

@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = ("group", "author", "created_at")

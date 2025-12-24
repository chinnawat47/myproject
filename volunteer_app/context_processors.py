from django.utils import timezone

def unread_notifications(request):
    """Context processor that adds unread notifications count for the current user."""
    count = 0
    user = getattr(request, 'user', None)
    try:
        if user and user.is_authenticated:
            # assume related manager `notifications` exists on user
            count = user.notifications.filter(is_read=False).count()
    except Exception:
        # be defensive: if notifications relation isn't present, return 0
        count = 0
    return {"unread_notifications_count": count}

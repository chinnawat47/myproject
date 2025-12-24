import logging
from typing import Optional, Sequence

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from ..models import Notification, NotificationPreference

logger = logging.getLogger(__name__)

CATEGORY_PREF_MAP = {
    "idea": "idea_updates",
    "activity": "activity_reminders",
    "hours": "hours_updates",
}


def get_or_create_pref(user) -> NotificationPreference:
    pref, _ = NotificationPreference.objects.get_or_create(user=user)
    return pref


def _should_send(pref: NotificationPreference, category: str, channel: str) -> bool:
    attr = CATEGORY_PREF_MAP.get(category)
    if attr and hasattr(pref, attr):
        enabled = getattr(pref, attr)
        if not enabled:
            return False
    if channel in ("email", "both"):
        return pref.email_enabled
    return pref.in_app_enabled


def notify_user(
    user,
    title: str,
    message: str,
    *,
    category: str = "general",
    target_url: Optional[str] = None,
    channel: str = "in_app",
    extra_data: Optional[dict] = None,
    email_override: bool = False,
) -> Optional[Notification]:
    """
    สร้างแจ้งเตือนให้ผู้ใช้ และส่งอีเมลถ้าจำเป็น

    channel: in_app, email, both
    """
    if not user or not user.is_authenticated:
        return None

    pref = get_or_create_pref(user)

    send_in_app = channel in ("in_app", "both") and pref.in_app_enabled
    send_email_flag = channel in ("email", "both") and pref.email_enabled

    attr = CATEGORY_PREF_MAP.get(category)
    if attr and not getattr(pref, attr, True):
        send_in_app = False
        send_email_flag = False

    if email_override:
        send_email_flag = pref.email_enabled

    if not (send_in_app or send_email_flag):
        return None

    notif = None
    if send_in_app:
        notif = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            category=category,
            target_url=target_url or "",
            data=extra_data or {},
            channel="both" if send_email_flag else "in_app",
        )

    if send_email_flag and user.email:
        _send_email_notification(user.email, title, message, target_url)

    return notif


def _send_email_notification(recipient: str, subject: str, message: str, target_url: Optional[str]):
    email_body = message
    if target_url:
        email_body += f"\n\nดูรายละเอียดเพิ่มเติม: {target_url}"

    try:
        send_mail(
            subject=subject,
            message=email_body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
            recipient_list=[recipient],
            fail_silently=True,
        )
    except Exception as exc:  # pragma: no cover - logging only
        logger.warning("ส่งอีเมลแจ้งเตือนไม่สำเร็จ: %s", exc)


def mark_notifications_read(user, notification_ids: Optional[Sequence[int]] = None):
    qs = user.notifications.filter(is_read=False)
    if notification_ids:
        qs = qs.filter(id__in=notification_ids)
    qs.update(is_read=True, read_at=timezone.now())


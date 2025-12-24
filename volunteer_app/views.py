from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum, Count, Exists, OuterRef
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse

from .forms import RegistrationForm, ActivityForm, SignupForm, IdeaForm, GroupForm, AdminLoginForm
from .models import (
    Activity, ActivitySignup, QRScan, IdeaProposal, IdeaVote,
    Group, GroupMembership, GroupPost, Role, Notification
)
from .utils import verify_qr_token
from .services.notification_service import notify_user, mark_notifications_read

import qrcode
from io import BytesIO
import base64

User = get_user_model()

# Helper to format activity details for JSON response
def get_activity_details(activity):
    """Return activity details for QR response display"""
    return {
        "id": activity.id,
        "title": activity.title,
        "datetime": activity.datetime.strftime("%d/%m/%Y %H:%M") if activity.datetime else None,
        "hours_reward": float(activity.hours_reward),
        "location": activity.location,
        "category": activity.category,
    }

# ------------------ Helper ------------------
def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    try:
        return user.has_role("admin", "staff", "leader")
    except AttributeError:
        return False

# ------------------ User Views ------------------
def index(request):
    """หน้าแรก - แสดงกิจกรรมล่าสุด"""
    # ดึงกิจกรรมล่าสุด 6 รายการ (ไม่รวม cancelled)
    recent_activities = Activity.objects.exclude(status="cancelled").order_by("-created_at")[:6]
    idea_queryset = (
        IdeaProposal.objects.filter(status="pending")
        .annotate(vote_total=Count("votes", distinct=True))
        .order_by("-vote_total", "-created_at")
    )
    if request.user.is_authenticated:
        idea_queryset = idea_queryset.annotate(
            user_voted=Exists(IdeaVote.objects.filter(idea=OuterRef("pk"), user=request.user))
        )
    top_ideas = list(idea_queryset[:3])
    if not request.user.is_authenticated:
        for idea in top_ideas:
            idea.user_voted = False

    return render(request, "index.html", {
        "recent_activities": recent_activities,
        "top_ideas": top_ideas,
    })


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email.split("@")[0]
            user.save()
            login(request, user)
            return redirect("volunteer_app:profile")
    else:
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})


def login_view(request):
    error = None
    username_value = ""
    if request.method == "POST":
        username_or_email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        remember_me = request.POST.get("remember-me")

        if not username_or_email or not password:
            error = "กรุณากรอกชื่อผู้ใช้/อีเมลและรหัสผ่าน"
            username_value = username_or_email
        else:
            user = None
            actual_username = None
            
            # ตรวจสอบว่ามี @ หรือไม่ เพื่อแยกแยะว่าเป็น email หรือ username
            is_email = "@" in username_or_email
            
            if is_email:
                # ถ้าเป็น email format ให้ค้นหา user จาก email
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    actual_username = user_obj.username
                except User.DoesNotExist:
                    # ถ้าไม่พบ email ให้ลองใช้ username โดยตรง
                    actual_username = username_or_email
                except User.MultipleObjectsReturned:
                    # ถ้ามี email ซ้ำกัน ให้ใช้ตัวแรก
                    user_obj = User.objects.filter(email=username_or_email).first()
                    if user_obj:
                        actual_username = user_obj.username
            else:
                # ถ้าไม่ใช่ email format ให้ลองค้นหา username ในฐานข้อมูลก่อน
                try:
                    user_obj = User.objects.get(username=username_or_email)
                    actual_username = user_obj.username
                except User.DoesNotExist:
                    # ถ้าไม่พบ username ให้ลองค้นหาจาก email (กรณีที่ username อาจเป็น email แต่ไม่มี @)
                    try:
                        user_obj = User.objects.get(email=username_or_email)
                        actual_username = user_obj.username
                    except (User.DoesNotExist, User.MultipleObjectsReturned):
                        actual_username = username_or_email
            
            # Authenticate ด้วย username ที่ได้
            if actual_username:
                user = authenticate(request, username=actual_username, password=password)

            if user:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                if user.is_superuser or user.is_staff:
                    return redirect("volunteer_app:admin_dashboard")
                return redirect("volunteer_app:profile")
            else:
                error = "กรุณาใส่ชื่อผู้ใช้หรือรหัสผ่านที่ถูกต้อง"
                username_value = username_or_email

    return render(request, "registration/login.html", {
        "error": error,
        "username": username_value
    })


def logout_view(request):
    logout(request)
    return redirect("volunteer_app:index")


@login_required
def profile(request):
    user = request.user
    signups = user.signups.select_related("activity").all()
    scans = user.qr_scans.select_related("activity").all()
    total_hours = user.total_hours()
    required_hours = 36
    remaining_hours = max(required_hours - total_hours, 0)
    has_completed_hours = total_hours >= required_hours
    return render(
        request,
        "profile.html",
        {
            "user": user,
            "signups": signups,
            "scans": scans,
            "total_hours": total_hours,
            "required_hours": required_hours,
            "remaining_hours": remaining_hours,
            "has_completed_hours": has_completed_hours,
        },
    )


@login_required
def edit_profile(request):
    """แก้ไขข้อมูลโปรไฟล์ผู้ใช้"""
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.title = request.POST.get("title", "").strip()
        user.faculty = request.POST.get("faculty", "").strip()
        user.department = request.POST.get("department", "").strip()
        year = request.POST.get("year", "").strip()
        if year:
            try:
                user.year = int(year)
            except ValueError:
                pass
        user.save()
        return redirect("volunteer_app:profile")
    
    return render(request, "edit_profile.html", {"user": request.user})


@login_required
def change_password(request):
    """เปลี่ยนรหัสผ่าน"""
    from django.contrib.auth import authenticate, update_session_auth_hash
    
    error = None
    if request.method == "POST":
        old_password = request.POST.get("old_password", "")
        new_password1 = request.POST.get("new_password1", "")
        new_password2 = request.POST.get("new_password2", "")
        
        user = request.user
        if not authenticate(username=user.username, password=old_password):
            error = "รหัสผ่านเก่าไม่ถูกต้อง"
        elif new_password1 != new_password2:
            error = "รหัสผ่านใหม่ไม่ตรงกัน"
        elif len(new_password1) < 8:
            error = "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"
        else:
            user.set_password(new_password1)
            user.save()
            update_session_auth_hash(request, user)
            return redirect("volunteer_app:profile")
    
    return render(request, "change_password.html", {"error": error})

# ------------------ Activity Views ------------------
def activities(request):
    from django.core.paginator import Paginator
    
    # Show all activities (including upcoming, ongoing, completed) - exclude only cancelled
    qs = Activity.objects.exclude(status="cancelled").order_by("-datetime")
    q = request.GET.get("q")
    category = request.GET.get("category")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    location = request.GET.get("location")
    faculty = request.GET.get("faculty")
    hours = request.GET.get("hours")

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category:
        qs = qs.filter(category=category)
    if date_from:
        qs = qs.filter(datetime__date__gte=date_from)
    if date_to:
        qs = qs.filter(datetime__date__lte=date_to)
    if location:
        qs = qs.filter(location__icontains=location)
    if faculty:
        qs = qs.filter(faculty__icontains=faculty)
    if hours:
        try:
            hours_val = float(hours)
            qs = qs.filter(hours_reward__gte=hours_val)
        except ValueError:
            pass

    # Pagination
    paginator = Paginator(qs, 9)  # 9 items per page
    page_number = request.GET.get('page', 1)
    activities = paginator.get_page(page_number)

    return render(request, "activities.html", {
        "activities": activities,
        "paginator": paginator,
        "is_paginated": activities.has_other_pages(),
    })


def activity_detail(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    user_signed = request.user.is_authenticated and ActivitySignup.objects.filter(activity=activity, user=request.user).exists()
    can_signup = not activity.is_full()
    qr_token = activity.qr_token()

    buffer = BytesIO()
    # generate QR for a confirm URL that includes signed token
    if qr_token:
        q = qrcode.make(request.build_absolute_uri(f"/qr/confirm/{qr_token}/"))
        q.save(buffer, format="PNG")
        qr_image_data = buffer.getvalue()
        qr_b64 = base64.b64encode(qr_image_data).decode()
    else:
        qr_b64 = None

    return render(
        request,
        "activity_detail.html",
        {
            "activity": activity,
            "user_signed": user_signed,
            "can_signup": can_signup,
            "qr_token": qr_token,
            "qr_b64": qr_b64
        }
    )


@login_required
@user_passes_test(is_admin)
def create_activity(request):
    if request.method == "POST":
        form = ActivityForm(request.POST, request.FILES)
        if form.is_valid():
            ac = form.save(commit=False)
            ac.created_by = request.user
            # Set default status to 'upcoming' if not set
            if not ac.status:
                ac.status = 'upcoming'
            ac.save()
            # Redirect to activities page to show the new activity
            return redirect("volunteer_app:activities")
    else:
        form = ActivityForm()
    return render(request, "create_activity.html", {"form": form})


@login_required
def activity_signup(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if ActivitySignup.objects.filter(activity=activity, user=request.user).exists():
        return HttpResponseBadRequest("คุณสมัครแล้ว")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            signup = form.save(commit=False)
            signup.activity = activity
            signup.user = request.user
            # determine status: confirm if space, else waitlist
            if activity.is_full():
                signup.status = "waitlist"
            else:
                signup.status = "confirmed"
            signup.save()
            return redirect("volunteer_app:activity_detail", pk=activity.pk)
    else:
        form = SignupForm()
    return render(request, "activity_detail.html", {"activity": activity, "form": form})


@login_required
def qr_scan_page(request):
    return render(request, "qr_scan.html", {})


@login_required
def qr_verify(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    token = request.POST.get("token") or request.POST.get("qr_token") or request.body.decode("utf-8")
    if not token:
        return JsonResponse({"ok": False, "code": "no_token", "message": "กรุณากรอกหรือสแกน QR code"})

    valid, activity_id = verify_qr_token(token)
    if not valid:
        return JsonResponse({
            "ok": False, 
            "code": "invalid_token",
            "message": "โทเค็นไม่ถูกต้องหรือหมดอายุแล้ว",
            "help": "กรุณาลองสแกน QR code ใหม่หรือติดต่อผู้ดูแลกิจกรรม"
        })

    try:
        activity = Activity.objects.get(pk=activity_id)
    except Activity.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "code": "activity_not_found",
            "message": "ไม่พบกิจกรรมนี้ในระบบ",
            "help": "กรุณาติดต่อผู้ดูแลระบบ"
        })

    # Check if activity is cancelled
    if activity.status == "cancelled":
        return JsonResponse({
            "ok": False,
            "code": "activity_cancelled",
            "message": "กิจกรรมนี้ถูกยกเลิกแล้ว",
            "help": "ไม่สามารถยืนยันชั่วโมงสำหรับกิจกรรมที่ถูกยกเลิกได้"
        })

    # require signup existence (any status) to allow scan
    if not ActivitySignup.objects.filter(activity=activity, user=request.user).exists():
        return JsonResponse({
            "ok": False,
            "code": "not_signed_up",
            "message": "คุณยังไม่ได้สมัครกิจกรรมนี้",
            "help": "กรุณาสมัครกิจกรรมก่อนจึงจะสามารถยืนยันได้",
            "activity": get_activity_details(activity)
        })

    # atomic create (idempotent)
    from django.db import transaction, IntegrityError
    earned_hours = float(activity.hours_reward)

    try:
        with transaction.atomic():
            scan, created = QRScan.objects.get_or_create(activity=activity, user=request.user, defaults={
                'token': token,
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:512],
                'device_id': request.POST.get('device_id') or request.headers.get('X-Device-Id'),
            })
            if not created:
                return JsonResponse({
                    "ok": False,
                    "code": "already_attended",
                    "message": "คุณยืนยันชั่วโมงกิจกรรมนี้แล้ว ได้ {:.1f} ชั่วโมง".format(activity.hours_reward),
                    "help": "หากเกิดข้อผิดพลาด กรุณาติดต่อผู้ดูแล",
                    "activity": get_activity_details(activity)
                })

            # mark signup as attended
            ActivitySignup.objects.filter(activity=activity, user=request.user).update(status='attended')
    except IntegrityError:
        return JsonResponse({
            "ok": False,
            "code": "database_error",
            "message": "เกิดข้อผิดพลาดในการบันทึก ลองอีกครั้ง",
            "help": "หากปัญหายังคงเกิดขึ้น โปรดติดต่อผู้ดูแลระบบ"
        }, status=500)

    notify_user(
        request.user,
        title="ยืนยันชั่วโมงกิจกรรมสำเร็จ",
        message=f"คุณได้รับ {earned_hours:.1f} ชั่วโมงจากกิจกรรม “{activity.title}”",
        category="hours",
        target_url=request.build_absolute_uri(reverse("volunteer_app:profile")),
    )

    return JsonResponse({
        "ok": True,
        "code": "success",
        "message": "ยืนยันสำเร็จ!",
        "hours_reward": earned_hours,
        "activity": get_activity_details(activity)
    })


def qr_confirm(request, token):
    """QR confirmation endpoint - can be accessed via direct URL"""
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next={request.path}")
    
    valid, activity_id = verify_qr_token(token)
    if not valid:
        return render(request, "qr_confirm_result.html", {
            "success": False,
            "message": "QR code ไม่ถูกต้องหรือหมดอายุ",
            "help": "กรุณาลองสแกน QR code ใหม่หรือติดต่อผู้ดูแลกิจกรรม"
        })
    
    try:
        activity = Activity.objects.get(pk=activity_id)
    except Activity.DoesNotExist:
        return render(request, "qr_confirm_result.html", {
            "success": False,
            "message": "ไม่พบกิจกรรมนี้ในระบบ",
            "help": "กรุณาติดต่อผู้ดูแลระบบ"
        })

    # Check if activity is cancelled
    if activity.status == "cancelled":
        return render(request, "qr_confirm_result.html", {
            "success": False,
            "message": "กิจกรรมนี้ถูกยกเลิกแล้ว",
            "help": "ไม่สามารถยืนยันชั่วโมงสำหรับกิจกรรมที่ถูกยกเลิกได้"
        })

    if not ActivitySignup.objects.filter(activity=activity, user=request.user).exists():
        return render(request, "qr_confirm_result.html", {
            "success": False,
            "message": "คุณยังไม่ได้สมัครกิจกรรมนี้",
            "help": "กรุณาสมัครกิจกรรมก่อนจึงจะสามารถยืนยันได้",
            "activity": activity
        })

    # Use atomic transaction and get_or_create to prevent duplicates
    from django.db import transaction, IntegrityError
    earned_hours = float(activity.hours_reward)

    try:
        with transaction.atomic():
            scan, created = QRScan.objects.get_or_create(
                activity=activity, 
                user=request.user, 
                defaults={
                    'token': token,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:512],
                }
            )
            if not created:
                return render(request, "qr_confirm_result.html", {
                    "success": False,
                    "message": f"คุณยืนยันชั่วโมงกิจกรรมนี้แล้ว ได้ {activity.hours_reward} ชั่วโมง",
                    "help": "หากเกิดข้อผิดพลาด กรุณาติดต่อผู้ดูแล",
                    "activity": activity
                })

            # mark signup as attended
            ActivitySignup.objects.filter(activity=activity, user=request.user).update(status='attended')
    except IntegrityError:
        return render(request, "qr_confirm_result.html", {
            "success": False,
            "message": "เกิดข้อผิดพลาดในการบันทึก ลองอีกครั้ง",
            "help": "หากปัญหายังคงเกิดขึ้น โปรดติดต่อผู้ดูแลระบบ"
        })

    notify_user(
        request.user,
        title="ยืนยันชั่วโมงกิจกรรมสำเร็จ",
        message=f"คุณได้รับ {earned_hours:.1f} ชั่วโมงจากกิจกรรม “{activity.title}”",
        category="hours",
        target_url=request.build_absolute_uri(reverse("volunteer_app:profile")),
    )

    return render(request, "qr_confirm_result.html", {
        "success": True,
        "message": f"ยืนยันสำเร็จ! คุณได้รับ {earned_hours} ชั่วโมงจิตอาสา",
        "activity": activity,
        "hours_reward": earned_hours
    })


# ------------------ Idea & Vote ------------------
@login_required
def idea_list(request):
    ideas = IdeaProposal.objects.all()
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if q:
        ideas = ideas.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if status and status in dict(IdeaProposal.STATUS_CHOICES):
        ideas = ideas.filter(status=status)

    ideas = ideas.annotate(
        vote_total=Count("votes", distinct=True),
        user_voted=Exists(IdeaVote.objects.filter(idea=OuterRef("pk"), user=request.user)),
    ).order_by("-vote_total", "-created_at")

    return render(request, "ideas_list.html", {
        "ideas": ideas,
        "q": q,
        "status": status,
        "status_choices": IdeaProposal.STATUS_CHOICES,
    })


@login_required
def propose_idea(request):
    if request.method == "POST":
        form = IdeaForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.proposer = request.user
            idea.save()
            return redirect("volunteer_app:idea_list")
    else:
        form = IdeaForm()
    return render(request, "propose_idea.html", {"form": form})


@login_required
@require_POST
def vote_idea(request, pk):
    idea = get_object_or_404(IdeaProposal, pk=pk)
    action = request.POST.get("action", "vote")

    if idea.status != "pending":
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "message": "ไอเดียนี้ปิดการโหวตแล้ว"}, status=400)
        return redirect("volunteer_app:idea_list")

    if action == "unvote":
        IdeaVote.objects.filter(idea=idea, user=request.user).delete()
        current_vote = False
    else:
        _, created = IdeaVote.objects.get_or_create(idea=idea, user=request.user)
        current_vote = True
        if not created:
            # already voted, keep state True
            pass
        else:
            if idea.proposer and idea.proposer != request.user:
                notify_user(
                    idea.proposer,
                    title="มีคนโหวตไอเดียของคุณ",
                    message=f"{request.user.get_full_name() or request.user.username} โหวตสนับสนุนไอเดีย “{idea.title}”",
                    category="idea",
                    target_url=request.build_absolute_uri(reverse("volunteer_app:idea_list")),
                )

    total_votes = idea.votes.count()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "voted": current_vote,
            "votes": total_votes,
        })

    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("volunteer_app:idea_list")


# ------------------ Notifications ------------------
@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    unread_count = notifications.filter(is_read=False).count()
    return render(request, "notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })


@login_required
@require_POST
def notification_mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.mark_read()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect(request.POST.get("next") or "volunteer_app:notifications")


@login_required
@require_POST
def notification_mark_all(request):
    mark_notifications_read(request.user)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect(request.POST.get("next") or "volunteer_app:notifications")

# ------------------ Group ------------------
@login_required
def groups_list(request):
    """หน้ารายชื่อกลุ่มทั้งหมด"""
    groups = Group.objects.all().order_by("-created_at")
    # เพิ่มข้อมูลว่า user เป็นสมาชิกของกลุ่มไหนบ้าง
    user_memberships = set(
        GroupMembership.objects.filter(user=request.user)
        .values_list('group_id', flat=True)
    )
    return render(request, "groups.html", {
        "groups": groups,
        "user_memberships": user_memberships
    })


@login_required
def create_group(request):
    """สร้างกลุ่มใหม่"""
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            g = form.save(commit=False)
            g.created_by = request.user
            g.save()
            g.generate_invite_code()
            GroupMembership.objects.create(group=g, user=request.user)
            return redirect("volunteer_app:group_detail", pk=g.pk)
    else:
        form = GroupForm()
    return render(request, "create_group.html", {"form": form})


@login_required
def group_detail(request, pk):
    """ดูรายละเอียดกลุ่ม / เข้าร่วม / โพสต์ / เชิญเพื่อน"""
    g = get_object_or_404(Group, pk=pk)
    user_in_group = GroupMembership.objects.filter(group=g, user=request.user).exists()

    # ✅ เข้าร่วมกลุ่ม
    if request.method == "POST" and "join_group" in request.POST:
        if not user_in_group:
            GroupMembership.objects.create(group=g, user=request.user)
            user_in_group = True
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": True,
                "message": "เข้าร่วมกลุ่มเรียบร้อย",
                "username": request.user.username,
                "full_name": request.user.get_full_name()
            })
        return redirect("volunteer_app:group_detail", pk=pk)

    # ✅ โพสต์ข้อความ
    if request.method == "POST" and "content" in request.POST:
        content = request.POST.get("content", "").strip()
        if content:
            post = GroupPost.objects.create(group=g, author=request.user, content=content)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "ok": True,
                    "author": request.user.get_full_name() or request.user.username,
                    "content": post.content,
                    "created_at": post.created_at.strftime("%d %b %Y, %H:%M")
                })
        return redirect("volunteer_app:group_detail", pk=pk)

    # ✅ เชิญเพื่อนเข้ากลุ่ม
    if request.method == "POST" and "invite_username" in request.POST:
        invite_username = request.POST.get("invite_username", "").strip()
        user_to_invite = User.objects.filter(username=invite_username).first()
        if not user_to_invite:
            return JsonResponse({"ok": False, "message": "ไม่พบบัญชีผู้ใช้นี้"})
        membership, created = GroupMembership.objects.get_or_create(group=g, user=user_to_invite)
        return JsonResponse({
            "ok": created,
            "message": "เชิญสำเร็จ" if created else "ผู้ใช้นี้อยู่ในกลุ่มแล้ว",
            "username": user_to_invite.username
        })

    # ✅ แสดงโพสต์และสมาชิกในกลุ่ม
    posts = g.posts.order_by("-created_at").all()
    members = g.memberships.select_related("user").all()

    return render(request, "group_detail.html", {
        "group": g,
        "posts": posts,
        "members": members,
        "user_in_group": user_in_group,
    })


@login_required
@require_POST
def join_group(request, pk):
    """รองรับ AJAX และ POST ปกติ เข้าร่วมกลุ่มโดยตรง"""
    g = get_object_or_404(Group, pk=pk)
    membership, created = GroupMembership.objects.get_or_create(group=g, user=request.user)
    
    # ถ้าเป็น AJAX request ให้ส่ง JSON response
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": created,
            "message": "เข้าร่วมกลุ่มแล้ว" if created else "คุณเป็นสมาชิกอยู่แล้ว"
        })
    
    # ถ้าเป็น POST ปกติ ให้ redirect กลับไปหน้ากลุ่ม
    if created:
        return redirect("volunteer_app:group_detail", pk=pk)
    else:
        return redirect("volunteer_app:groups")



# ------------------ Chatbot ------------------
@require_POST
def chatbot_api(request):
    q = request.POST.get("q", "").strip().lower()
    
    # ตรวจสอบคำถามเกี่ยวกับกิจกรรม
    if any(keyword in q for keyword in ["มีกิจกรรม", "กิจกรรมอะไร", "กิจกรรม", "activity", "กิจกรรมทั้งหมด"]):
        activity_count = Activity.objects.exclude(status="cancelled").count()
        if activity_count > 0:
            resp = f"ตอนนี้มีกิจกรรมทั้งหมด {activity_count} กิจกรรมที่เปิดรับสมัครอยู่ คุณสามารถเข้าไปดูรายละเอียดและสมัครได้ที่หน้า 'กิจกรรมทั้งหมด' 🎯"
        else:
            resp = "ตอนนี้ยังไม่มีกิจกรรมที่เปิดรับสมัคร แต่จะมีกิจกรรมใหม่ๆ เร็วๆ นี้ ติดตามได้ที่หน้า 'กิจกรรมทั้งหมด' 📅"
    
    # ตรวจสอบคำถามเกี่ยวกับการสมัคร
    elif any(keyword in q for keyword in ["สมัครอย่างไร", "สมัคร", "วิธีสมัคร", "register", "signup", "เข้าร่วม"]):
        resp = """📝 วิธีการสมัครกิจกรรมจิตอาสา:
        
1. เข้าไปที่หน้า 'กิจกรรมทั้งหมด'
2. เลือกกิจกรรมที่คุณสนใจ
3. กดปุ่ม 'สมัคร' หรือ 'สมัครเข้าร่วม'
4. กรอกข้อมูลเพิ่มเติม (ถ้ามี)
5. กดส่งเพื่อยืนยันการสมัคร

หลังจากสมัครแล้ว คุณจะได้รับอีเมลยืนยันและสามารถตรวจสอบสถานะได้ในโปรไฟล์ของคุณ ✅"""
    
    # ตรวจสอบคำถามเกี่ยวกับชั่วโมง
    elif any(keyword in q for keyword in ["ได้กี่ชั่วโมง", "ชั่วโมง", "hours", "hour", "ชั่วโมงจิตอาสา"]):
        resp = """⏰ เกี่ยวกับชั่วโมงจิตอาสา:
        
• ชั่วโมงที่ได้รับจะแสดงในรายละเอียดของแต่ละกิจกรรม
• คุณจะได้รับชั่วโมงเมื่อสแกน QR Code หน้างาน
• แต่ละกิจกรรมจะให้ชั่วโมงแตกต่างกันตามประเภทและระยะเวลา
• คุณสามารถตรวจสอบชั่วโมงรวมทั้งหมดได้ในหน้าโปรไฟล์

💡 หมายเหตุ: แต่ละกิจกรรมสามารถสแกน QR ได้เพียงครั้งเดียวต่อผู้ใช้"""
    
    # ตรวจสอบคำถามเกี่ยวกับ QR Code
    elif any(keyword in q for keyword in ["qr", "qr code", "สแกน", "ยืนยัน", "scan", "qrcode"]):
        resp = """📱 การสแกน QR Code:
        
1. เข้าไปที่หน้า 'สแกน QR ยืนยันชั่วโมง'
2. เปิดกล้องหรือเลือกไฟล์ QR Code
3. สแกน QR Code ที่ได้รับจากหน้างานกิจกรรม
4. ระบบจะยืนยันและบันทึกชั่วโมงให้อัตโนมัติ

⚠️ หมายเหตุ: ต้องสมัครกิจกรรมก่อนจึงจะสามารถสแกน QR ได้"""
    
    # ตรวจสอบคำถามเกี่ยวกับโปรไฟล์
    elif any(keyword in q for keyword in ["โปรไฟล์", "profile", "ข้อมูลส่วนตัว", "ชั่วโมงรวม"]):
        resp = """👤 เกี่ยวกับโปรไฟล์:
        
คุณสามารถ:
• ดูข้อมูลส่วนตัวของคุณ
• ตรวจสอบชั่วโมงจิตอาสารวมทั้งหมด
• ดูประวัติการเข้าร่วมกิจกรรม
• แก้ไขข้อมูลส่วนตัว
• เปลี่ยนรหัสผ่าน

เข้าไปได้ที่เมนู 'โปรไฟล์' หรือคลิกที่ชื่อของคุณ"""
    
    # ตรวจสอบคำถามทักทาย
    elif any(keyword in q for keyword in ["สวัสดี", "hello", "hi", "หวัดดี", "ดี", "hey"]):
        resp = "สวัสดีครับ! 👋 ยินดีต้อนรับสู่ระบบจิตอาสา ผมพร้อมช่วยเหลือคุณเสมอ ถ้ามีคำถามอะไรถามได้เลยนะครับ 😊"
    
    # ตรวจสอบคำถามขอบคุณ
    elif any(keyword in q for keyword in ["ขอบคุณ", "thank", "thanks", "ขอบใจ"]):
        resp = "ยินดีครับ! 😊 ถ้ามีคำถามอื่นๆ อีก สามารถถามได้ตลอดเวลาเลยนะครับ"
    
    # คำถามอื่นๆ
    else:
        resp = """ขอโทษครับ ฉันยังไม่เข้าใจคำถามนี้ 😅

คำถามที่รองรับ:
• 📋 มีกิจกรรมอะไรบ้าง?
• 📝 สมัครอย่างไร?
• ⏰ ได้กี่ชั่วโมง?
• 📱 วิธีสแกน QR Code?
• 👤 ดูโปรไฟล์

ลองถามใหม่ด้วยคำถามเหล่านี้ดูนะครับ หรือใช้ปุ่มคำถามยอดนิยมด้านล่างได้เลย! 💡"""
    
    return JsonResponse({"reply": resp})


# ------------------ Admin Views ------------------
def admin_login(request):
    error = None
    next_url = request.GET.get("next", "volunteer_app:admin_dashboard")
    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data["username"].strip()
            password = form.cleaned_data["password"]
            
            user = None
            
            # Try to authenticate with username first
            user = authenticate(request, username=username_or_email, password=password)
            
            # If not successful and input contains @, try with email
            if not user and "@" in username_or_email:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user and (user.is_staff or user.is_superuser):
                login(request, user)
                return redirect(next_url)
            else:
                error = "ชื่อผู้ใช้/อีเมลหรือรหัสผ่านไม่ถูกต้อง หรือไม่ใช่ Admin"
    else:
        form = AdminLoginForm()
    return render(request, "admin_login.html", {"form": form, "error": error})


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_dashboard(request):
    from datetime import timedelta
    
    total_users = User.objects.count()
    # Calculate total hours from QR scans (actual volunteer hours)
    total_hours = sum(scan.activity.hours_reward for scan in QRScan.objects.select_related('activity').all())
    total_signups = ActivitySignup.objects.count()
    total_qr_scans = QRScan.objects.count()
    total_activities = Activity.objects.count()
    pending_ideas = IdeaProposal.objects.filter(status="pending").count()
    
    # Activity statistics by status
    activities_upcoming = Activity.objects.filter(status="upcoming").count()
    activities_ongoing = Activity.objects.filter(status="ongoing").count()
    activities_completed = Activity.objects.filter(status="completed").count()
    
    # Time-based statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
    qr_scans_today = QRScan.objects.filter(scanned_at__date=today).count()
    qr_scans_week = QRScan.objects.filter(scanned_at__date__gte=week_ago).count()
    
    # Recent items
    recent_activities = Activity.objects.order_by('-created_at')[:5]
    upcoming_activities = Activity.objects.filter(status="upcoming", datetime__gte=timezone.now()).order_by('datetime')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    pending_ideas_list = IdeaProposal.objects.filter(status='pending').order_by('-created_at')[:5]
    recent_qr_scans = QRScan.objects.select_related('user', 'activity').order_by('-scanned_at')[:20]
    
    # User hours summary - top users by volunteer hours
    users_with_hours = []
    for user in User.objects.all():
        hours = user.total_hours()
        if hours > 0:
            users_with_hours.append({
                'user': user,
                'total_hours': hours,
                'scan_count': user.qr_scans.count()
            })
    users_with_hours.sort(key=lambda x: x['total_hours'], reverse=True)
    top_users = users_with_hours[:10]  # Top 10 users

    return render(request, "admin_dashboard.html", {
        "total_users": total_users,
        "total_hours": total_hours,
        "total_signups": total_signups,
        "total_qr_scans": total_qr_scans,
        "total_activities": total_activities,
        "pending_ideas": pending_ideas,
        "activities_upcoming": activities_upcoming,
        "activities_ongoing": activities_ongoing,
        "activities_completed": activities_completed,
        "new_users_today": new_users_today,
        "new_users_week": new_users_week,
        "qr_scans_today": qr_scans_today,
        "qr_scans_week": qr_scans_week,
        "recent_activities": recent_activities,
        "upcoming_activities": upcoming_activities,
        "recent_users": recent_users,
        "pending_ideas_list": pending_ideas_list,
        "recent_qr_scans": recent_qr_scans,
        "top_users": top_users,
    })


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_manage_activities(request):
    """จัดการกิจกรรมทั้งหมด (ดู/แก้ไข/ลบ)"""
    activities = Activity.objects.all().order_by("-created_at")
    return render(request, "admin_manage_activities.html", {"activities": activities})


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_edit_activity(request, pk):
    """แก้ไขกิจกรรม"""
    activity = get_object_or_404(Activity, pk=pk)
    
    if request.method == "POST":
        activity.title = request.POST.get("title", activity.title)
        activity.description = request.POST.get("description", activity.description)
        activity.category = request.POST.get("category", activity.category)
        activity.status = request.POST.get("status", activity.status)
        activity.location = request.POST.get("location", activity.location)
        activity.capacity = int(request.POST.get("capacity", activity.capacity))
        activity.hours_reward = float(request.POST.get("hours_reward", activity.hours_reward))
        
        if request.FILES.get("image"):
            activity.image = request.FILES["image"]
        
        activity.save()
        return redirect("volunteer_app:admin_manage_activities")
    
    return render(request, "admin_edit_activity.html", {"activity": activity})


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
@require_POST
def admin_delete_activity(request, pk):
    """ลบกิจกรรม"""
    activity = get_object_or_404(Activity, pk=pk)
    activity.delete()
    return redirect("volunteer_app:admin_manage_activities")


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_manage_ideas(request):
    """ดูและจัดการ idea proposals"""
    ideas = IdeaProposal.objects.all().order_by("-created_at")
    return render(request, "admin_manage_ideas.html", {"ideas": ideas})


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_manage_users(request):
    """จัดการผู้ใช้ทั้งหมด"""
    users = User.objects.all().prefetch_related("roles").order_by("-date_joined")
    return render(request, "admin_manage_users.html", {"users": users})


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_edit_user(request, pk):
    """แก้ไขข้อมูลผู้ใช้"""
    user = get_object_or_404(User, pk=pk)
    roles = Role.objects.filter(is_assignable=True).order_by("display_order", "name")
    
    if request.method == "POST":
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.is_staff = request.POST.get("is_staff") == "on"
        user.is_superuser = request.POST.get("is_superuser") == "on"
        user.save()

        selected_role_ids = request.POST.getlist("roles")
        if selected_role_ids:
            selected_roles = Role.objects.filter(id__in=selected_role_ids)
            user.roles.set(selected_roles)
        else:
            default_role = Role.objects.filter(code="user").first()
            if default_role:
                user.roles.set([default_role])

        user.sync_admin_flags_from_roles()
        user.save()
        return redirect("volunteer_app:admin_manage_users")
    
    return render(request, "admin_edit_user.html", {
        "user": user,
        "roles": roles,
        "user_role_ids": set(user.roles.values_list("id", flat=True)),
    })


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
@require_POST
def admin_delete_user(request, pk):
    """ลบผู้ใช้"""
    user = get_object_or_404(User, pk=pk)
    if user != request.user:  # ป้องกันการลบตัวเองหลังสุด
        user.delete()
    return redirect("volunteer_app:admin_manage_users")


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
@require_POST
def admin_approve_idea(request, pk):
    """อนุมัติ idea proposal"""
    idea = get_object_or_404(IdeaProposal, pk=pk)
    idea.status = "approved"
    idea.reviewed = True
    idea.save()

    if idea.proposer:
        notify_user(
            idea.proposer,
            title="ไอเดียของคุณได้รับการอนุมัติ",
            message=f"ไอเดีย “{idea.title}” ถูกอนุมัติโดยทีมงานแล้ว เตรียมรออัปเดตกิจกรรมได้เลย!",
            category="idea",
            target_url=request.build_absolute_uri(reverse("volunteer_app:idea_list")),
        )
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "message": "อนุมัติ idea แล้ว"})
    return redirect("volunteer_app:admin_manage_ideas")


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
@require_POST
def admin_reject_idea(request, pk):
    """ปฏิเสธ idea proposal"""
    idea = get_object_or_404(IdeaProposal, pk=pk)
    idea.status = "rejected"
    idea.reviewed = True
    idea.save()

    if idea.proposer:
        notify_user(
            idea.proposer,
            title="ไอเดียของคุณไม่ได้รับการอนุมัติ",
            message=f"ขออภัย ไอเดีย “{idea.title}” ยังไม่สามารถดำเนินการได้ หากมีคำถามเพิ่มเติมติดต่อทีมงานได้เลยนะ",
            category="idea",
            target_url=request.build_absolute_uri(reverse("volunteer_app:idea_list")),
        )
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "message": "ปฏิเสธ idea แล้ว"})
    return redirect("volunteer_app:admin_manage_ideas")


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
@require_POST
def admin_delete_qr_scan(request, pk):
    """ลบ QR scan (ลบชั่วโมงจิตอาสา)"""
    scan = get_object_or_404(QRScan, pk=pk)
    user = scan.user
    activity = scan.activity
    scan.delete()
    
    # Update signup status back to confirmed if exists
    signup = ActivitySignup.objects.filter(activity=activity, user=user).first()
    if signup and signup.status == 'attended':
        signup.status = 'confirmed'
        signup.save()
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "message": f"ลบชั่วโมงจิตอาสา {activity.hours_reward} ชั่วโมง ของ {user.get_full_name() or user.username} แล้ว"})
    return redirect("volunteer_app:admin_dashboard")


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_add_volunteer_hours(request):
    """เพิ่มชั่วโมงจิตอาสาให้ผู้ใช้"""
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        activity_id = request.POST.get("activity_id")
        
        if not user_id or not activity_id:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "message": "กรุณาเลือกผู้ใช้และกิจกรรม"})
            return redirect("volunteer_app:admin_dashboard")
        
        try:
            user = User.objects.get(pk=user_id)
            activity = Activity.objects.get(pk=activity_id)
            
            # Check if QR scan already exists
            scan, created = QRScan.objects.get_or_create(
                activity=activity,
                user=user,
                defaults={
                    'token': activity.qr_token() or 'admin_manual',
                    'scanned_from_staff': True,
                    'ip_address': request.META.get('REMOTE_ADDR'),
                }
            )
            
            if created:
                # Update signup status to attended if exists
                signup = ActivitySignup.objects.filter(activity=activity, user=user).first()
                if signup:
                    signup.status = 'attended'
                    signup.save()
                
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({
                        "ok": True, 
                        "message": f"เพิ่มชั่วโมงจิตอาสา {activity.hours_reward} ชั่วโมง ให้ {user.get_full_name() or user.username} แล้ว"
                    })
            else:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({
                        "ok": False, 
                        "message": f"{user.get_full_name() or user.username} มีชั่วโมงจิตอาสาจากกิจกรรมนี้แล้ว"
                    })
            
        except (User.DoesNotExist, Activity.DoesNotExist):
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "message": "ไม่พบผู้ใช้หรือกิจกรรม"})
        
        return redirect("volunteer_app:admin_dashboard")
    
    # GET request - show form
    users = User.objects.all().order_by('username')
    activities = Activity.objects.exclude(status='cancelled').order_by('-datetime')
    
    return render(request, "admin_add_hours.html", {
        "users": users,
        "activities": activities,
    })


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_view_user_hours(request, user_id):
    """ดูรายละเอียดชั่วโมงจิตอาสาของผู้ใช้"""
    user = get_object_or_404(User, pk=user_id)
    scans = user.qr_scans.select_related('activity').order_by('-scanned_at')
    total_hours = user.total_hours()
    
    return render(request, "admin_user_hours.html", {
        "user": user,
        "scans": scans,
        "total_hours": total_hours,
    })


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_logout(request):
    logout(request)
    return redirect("volunteer_app:admin_login")


# ------------------- Error Handlers -------------------
def error_404(request, exception=None):
    """หน้า 404 - ไม่พบหน้านี้"""
    return render(request, "404.html", status=404)


def error_500(request):
    """หน้า 500 - ข้อผิดพลาดเซิร์ฟเวอร์"""
    return render(request, "500.html", status=500)

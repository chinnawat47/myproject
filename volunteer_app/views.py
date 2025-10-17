from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_POST

from .forms import RegistrationForm, ActivityForm, SignupForm, IdeaForm, GroupForm, AdminLoginForm
from .models import (
    Activity, ActivitySignup, QRScan, Vote, IdeaProposal,
    Group, GroupMembership, GroupPost
)

import qrcode
from io import BytesIO
import base64

User = get_user_model()

# ------------------ Helper ------------------
def is_admin(user):
    return user.is_staff or user.is_superuser

# ------------------ User Views ------------------
def index(request):
    return render(request, "index.html")


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

        username = None
        if "@" in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = None
        else:
            username = username_or_email

        if username:
            user = authenticate(request, username=username, password=password)
        else:
            user = None

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
    return render(request, "profile.html", {"user": user, "signups": signups, "scans": scans, "total_hours": total_hours})

# ------------------ Activity Views ------------------
def activities(request):
    qs = Activity.objects.all().order_by("datetime")
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

    return render(request, "activities.html", {"activities": qs})


def activity_detail(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    user_signed = request.user.is_authenticated and ActivitySignup.objects.filter(activity=activity, user=request.user).exists()
    can_signup = not activity.is_full()
    qr_token = activity.qr_token()

    buffer = BytesIO()
    q = qrcode.make(request.build_absolute_uri(f"/qr/confirm/{qr_token}/"))
    q.save(buffer, format="PNG")
    qr_image_data = buffer.getvalue()
    qr_b64 = base64.b64encode(qr_image_data).decode()

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
def create_activity(request):
    if request.method == "POST":
        form = ActivityForm(request.POST, request.FILES)
        if form.is_valid():
            ac = form.save(commit=False)
            ac.created_by = request.user
            ac.save()
            return redirect("volunteer_app:activity_detail", pk=ac.pk)
    else:
        form = ActivityForm()
    return render(request, "create_activity.html", {"form": form})


@login_required
def activity_signup(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if activity.is_full():
        return HttpResponseBadRequest("กิจกรรมเต็มแล้ว")
    if ActivitySignup.objects.filter(activity=activity, user=request.user).exists():
        return HttpResponseBadRequest("คุณสมัครแล้ว")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            signup = form.save(commit=False)
            signup.activity = activity
            signup.user = request.user
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
    token = request.POST.get("token") or request.body.decode("utf-8")
    token = request.POST.get("token", request.POST.get("qr_token", token))
    if not token:
        return JsonResponse({"ok": False, "message": "token missing"})

    try:
        activity = next(a for a in Activity.objects.all() if a.qr_token() == token)
    except StopIteration:
        return JsonResponse({"ok": False, "message": "QR code ไม่ถูกต้อง"})

    if not ActivitySignup.objects.filter(activity=activity, user=request.user).exists():
        return JsonResponse({"ok": False, "message": "ยังไม่ได้สมัครกิจกรรมนี้"})
    if QRScan.objects.filter(activity=activity, user=request.user).exists():
        return JsonResponse({"ok": False, "message": "คุณยืนยันชั่วโมงกิจกรรมนี้แล้ว"})

    QRScan.objects.create(activity=activity, user=request.user, token=token)
    return JsonResponse({"ok": True, "message": f"ยืนยันสำเร็จ: ได้ {activity.hours_reward} ชั่วโมง"})


def qr_confirm(request, token):
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next={request.path}")

    activity = next((a for a in Activity.objects.all() if a.qr_token() == token), None)
    if activity is None:
        return HttpResponse("QR code ไม่ถูกต้อง")
    if not ActivitySignup.objects.filter(activity=activity, user=request.user).exists():
        return HttpResponse("คุณยังไม่ได้สมัครกิจกรรมนี้")
    if QRScan.objects.filter(activity=activity, user=request.user).exists():
        return HttpResponse("คุณยืนยันแล้ว")

    QRScan.objects.create(activity=activity, user=request.user, token=token)
    return HttpResponse(f"ยืนยันสำเร็จ: ได้ {activity.hours_reward} ชั่วโมง")


# ------------------ Idea & Vote ------------------
@login_required
def propose_idea(request):
    if request.method == "POST":
        form = IdeaForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.proposer = request.user
            idea.save()
            return redirect("volunteer_app:activities")
    else:
        form = IdeaForm()
    return render(request, "propose_idea.html", {"form": form})


@login_required
def vote_activity(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id)
    vote, created = Vote.objects.get_or_create(activity=activity, user=request.user)
    if not created:
        return JsonResponse({"ok": False, "message": "คุณโหวตแล้ว"})
    return JsonResponse({"ok": True, "message": "โหวตแล้ว"})

# ------------------ Group ------------------
@login_required
def groups_list(request):
    """หน้ารายชื่อกลุ่มทั้งหมด"""
    groups = Group.objects.all().order_by("-created_at")
    return render(request, "groups.html", {"groups": groups})


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
def join_group(request, pk):
    """รองรับ AJAX เข้าร่วมกลุ่มโดยตรง"""
    g = get_object_or_404(Group, pk=pk)
    membership, created = GroupMembership.objects.get_or_create(group=g, user=request.user)
    return JsonResponse({
        "ok": created,
        "message": "เข้าร่วมกลุ่มแล้ว" if created else "คุณเป็นสมาชิกอยู่แล้ว"
    })



# ------------------ Chatbot ------------------
@require_POST
def chatbot_api(request):
    q = request.POST.get("q", "").strip().lower()
    if "มีกิจกรรม" in q or "กิจกรรมอะไร" in q:
        resp = "ตอนนี้มีกิจกรรมที่ลงไว้บนหน้า 'กิจกรรมทั้งหมด' คุณสามารถใช้ตัวกรองหรือค้นหาเพื่อดูรายละเอียดได้"
    elif "สมัครอย่างไร" in q or "สมัคร" in q:
        resp = "เข้าสู่หน้ากิจกรรม เลือกกิจกรรมที่ต้องการ แล้วกดปุ่ม 'สมัคร' กรอกข้อมูลเพิ่มเติมแล้วส่งได้เลย"
    elif "ได้กี่ชั่วโมง" in q or "ชั่วโมง" in q:
        resp = "ชั่วโมงที่ได้รับจะแสดงในรายละเอียดกิจกรรม (hours_reward) และจะยืนยันเมื่อสแกน QR หน้างานครั้งเดียวต่อผู้ใช้"
    else:
        resp = "ขอโทษ ฉันยังไม่เข้าใจคำถามนี้ — ตัวอย่างคำถามที่รองรับ: 'มีกิจกรรมอะไรบ้าง?', 'สมัครอย่างไร?', 'ได้กี่ชั่วโมง?'"
    return JsonResponse({"reply": resp})


# ------------------ Admin Views ------------------
def admin_login(request):
    error = None
    next_url = request.GET.get("next", "volunteer_app:admin_dashboard")
    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user and (user.is_staff or user.is_superuser):
                login(request, user)
                return redirect(next_url)
            else:
                error = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง หรือไม่ใช่ Admin"
    else:
        form = AdminLoginForm()
    return render(request, "admin_login.html", {"form": form, "error": error})


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_dashboard(request):
    total_users = User.objects.count()
    total_hours = ActivitySignup.objects.aggregate(total=Sum("activity__hours_reward"))["total"] or 0
    total_signups = ActivitySignup.objects.count()
    total_qr_scans = QRScan.objects.count()
    return render(request, "admin_dashboard.html", {
        "total_users": total_users,
        "total_hours": total_hours,
        "total_signups": total_signups,
        "total_qr_scans": total_qr_scans,
    })


@login_required(login_url="/admin/login/")
@user_passes_test(is_admin, login_url="/admin/login/")
def admin_logout(request):
    logout(request)
    return redirect("volunteer_app:admin_login")

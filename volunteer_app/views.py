from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_POST

from .forms import RegistrationForm, ActivityForm, SignupForm, IdeaForm, GroupForm
from .models import (
    Activity, ActivitySignup, QRScan, Vote, IdeaProposal,
    Group, GroupMembership, GroupPost
)

import qrcode
from io import BytesIO
import base64

# ใช้ Custom User model
User = get_user_model()


def index(request):
    return render(request, "index.html")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email.split("@")[0]  # ตั้ง username จาก email
            user.save()
            login(request, user)
            return redirect("volunteer_app:profile")
    else:
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})


def login_view(request):
    error = None
    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")

        username = None
        # รองรับการ login ด้วย email
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

        if user is not None:
            login(request, user)
            return redirect("volunteer_app:profile")
        else:
            error = "กรุณาใส่ ชื่อผู้ใช้ หรือรหัสผ่านที่ถูกต้อง"

    return render(request, "registration/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("volunteer_app:index")


def activities(request):
    qs = Activity.objects.all().order_by("datetime")
    # Filters
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
    user_signed = False
    if request.user.is_authenticated:
        user_signed = ActivitySignup.objects.filter(activity=activity, user=request.user).exists()
    can_signup = not activity.is_full()
    qr_token = activity.qr_token()

    # generate QR image
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


@login_required
def profile(request):
    user = request.user
    signups = user.signups.select_related("activity").all()
    scans = user.qr_scans.select_related("activity").all()
    total_hours = user.total_hours()
    return render(request, "profile.html", {"user": user, "signups": signups, "scans": scans, "total_hours": total_hours})


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


def groups_list(request):
    groups = Group.objects.all()
    return render(request, "groups.html", {"groups": groups})


@login_required
def create_group(request):
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            g = form.save(commit=False)
            g.created_by = request.user
            g.generate_invite_code()
            g.save()
            GroupMembership.objects.create(group=g, user=request.user)
            return redirect("volunteer_app:group_detail", pk=g.pk)
    else:
        form = GroupForm()
    return render(request, "group_detail.html", {"form": form})


def group_detail(request, pk):
    g = get_object_or_404(Group, pk=pk)
    posts = g.posts.order_by("-created_at").all()
    members = g.memberships.select_related("user").all()
    return render(request, "group_detail.html", {"group": g, "posts": posts, "members": members})


@login_required
def join_group(request, pk):
    g = get_object_or_404(Group, pk=pk)
    code = request.GET.get("code")
    if code and code == g.code:
        GroupMembership.objects.get_or_create(group=g, user=request.user)
        return redirect("volunteer_app:group_detail", pk=g.pk)
    return HttpResponseBadRequest("รหัสเชิญไม่ถูกต้อง")

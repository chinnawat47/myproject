from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Activity, ActivitySignup, IdeaProposal, GroupPost, Group
from django.core.exceptions import ValidationError
import re
from django.utils import timezone

UBU_EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@ubu\.ac\.th$'

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    title = forms.CharField(required=True, max_length=20, label="คำนำหน้า")
    student_id = forms.CharField(required=True, max_length=20)
    faculty = forms.CharField(required=True)
    department = forms.CharField(required=True)
    year = forms.IntegerField(required=True, min_value=1, max_value=10)

    class Meta:
        model = User
        fields = ("username", "email", "title", "first_name", "last_name", "student_id", "faculty", "department", "year", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not re.match(UBU_EMAIL_REGEX, email):
            raise ValidationError("ต้องใช้อีเมลของมหาวิทยาลัยเท่านั้น (ลงท้ายด้วย @ubu.ac.th)")
        return email

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["title", "description", "category", "datetime", "location", "capacity", "hours_reward", "image"]

        widgets = {
            "datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_datetime(self):
        dt = self.cleaned_data.get("datetime")
        if dt and dt < timezone.now():
            raise forms.ValidationError("วันที่/เวลาต้องเป็นอนาคต")
        return dt

class SignupForm(forms.ModelForm):
    class Meta:
        model = ActivitySignup
        fields = ["note"]

class IdeaForm(forms.ModelForm):
    class Meta:
        model = IdeaProposal
        fields = ["title", "description", "target_hours"]

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "description"]

# ---------------- Admin Login Form ----------------
class AdminLoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="ชื่อผู้ใช้")
    password = forms.CharField(widget=forms.PasswordInput, label="รหัสผ่าน")

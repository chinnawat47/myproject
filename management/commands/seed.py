from django.core.management.base import BaseCommand
from volunteer_app.models import User, Activity, ActivitySignup, Group
from django.utils import timezone
import datetime
import random

class Command(BaseCommand):
    help = "Seed demo users, activities, and groups"

    def handle(self, *args, **options):
        # Create demo users
        if not User.objects.filter(email="demo@ubu.ac.th").exists():
            u = User.objects.create_user(username="demo", email="demo@ubu.ac.th", password="demo12345", first_name="Demo", last_name="User", title="นาย", student_id="6500001", faculty="บริหาร", department="การจัดการ", year=4)
            print("Created demo user demo@ubu.ac.th / demo12345")
        else:
            u = User.objects.get(email="demo@ubu.ac.th")
            print("Demo user exists")

        # Activities
        if Activity.objects.count() == 0:
            for i in range(1,6):
                a = Activity.objects.create(
                    title=f"กิจกรรมตัวอย่าง #{i}",
                    description="กิจกรรมสำหรับการสาธิตระบบ",
                    category=random.choice(["community","education","environment","health","other"]),
                    datetime=timezone.now() + datetime.timedelta(days=i),
                    location=f"สถานที่ {i}",
                    capacity=10 + i,
                    hours_reward=1.5
                )
                print("Created activity", a.title)
        else:
            print("Activities exist")

        # Create a group
        if Group.objects.count() == 0:
            g = Group.objects.create(name="กลุ่มตัวอย่าง", description="กลุ่มสำหรับทดสอบ", created_by=u, code="invite123")
            print("Created group", g.name)
        else:
            print("Groups exist")

        print("Seeding done.")

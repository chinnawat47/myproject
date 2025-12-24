from django.db import migrations, models


def seed_roles(apps, schema_editor):
    Role = apps.get_model("volunteer_app", "Role")
    User = apps.get_model("volunteer_app", "User")

    role_specs = [
        {
            "code": "admin",
            "name": "Admin",
            "description": "จัดการระบบทั้งหมดและกำหนดสิทธิ์ผู้ใช้",
            "display_order": 10,
        },
        {
            "code": "staff",
            "name": "Staff",
            "description": "เจ้าหน้าที่ระบบ/เจ้าหน้าที่กิจกรรม",
            "display_order": 20,
        },
        {
            "code": "leader",
            "name": "Leader",
            "description": "หัวหน้ากิจกรรม ดูแลอาสาสมัครภาคสนาม",
            "display_order": 30,
        },
        {
            "code": "reviewer",
            "name": "Reviewer",
            "description": "ตรวจสอบข้อเสนอไอเดียและ feedback",
            "display_order": 40,
        },
        {
            "code": "user",
            "name": "User",
            "description": "ผู้ใช้งานทั่วไป",
            "display_order": 100,
        },
    ]

    role_map = {}
    for spec in role_specs:
        role, _ = Role.objects.get_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "description": spec["description"],
                "display_order": spec["display_order"],
            },
        )
        role_map[spec["code"]] = role

    default_role = role_map.get("user")

    for user in User.objects.all():
        assigned_codes = []
        if user.is_superuser:
            assigned_codes.extend(["admin", "staff"])
        elif user.is_staff or getattr(user, "is_admin", False):
            assigned_codes.append("staff")

        if not assigned_codes and default_role:
            assigned_codes.append("user")

        roles_to_assign = [role_map[code] for code in assigned_codes if code in role_map]
        if default_role and default_role not in roles_to_assign:
            roles_to_assign.append(default_role)

        if roles_to_assign:
            user.roles.add(*roles_to_assign)

        if {"admin", "staff"} & set(assigned_codes):
            user.is_admin = True
            if not user.is_staff:
                user.is_staff = True
            user.save(update_fields=["is_admin", "is_staff"])


class Migration(migrations.Migration):

    dependencies = [
        ("volunteer_app", "0005_remove_vote_create_ideavote"),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("display_order", models.PositiveSmallIntegerField(default=100)),
                ("is_assignable", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["display_order", "name"],
            },
        ),
        migrations.AddField(
            model_name="user",
            name="roles",
            field=models.ManyToManyField(blank=True, related_name="users", to="volunteer_app.role"),
        ),
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]


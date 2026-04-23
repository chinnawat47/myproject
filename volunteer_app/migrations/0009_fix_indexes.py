# Generated migration to fix duplicate index names

from django.db import migrations, models


def remove_old_indexes_safely(apps, schema_editor):
    """Safely remove old indexes if they exist."""
    indexes_to_remove = [
        'volunteer_a_datetim_idx',
        'volunteer_a_status_idx',
        'volunteer_a_email_idx',
        'volunteer_a_email_v_idx',
        'volunteer_a_scanned_idx',
        'volunteer_a_token_idx',
        'volunteer_a_expires_idx',
    ]
    
    with schema_editor.connection.cursor() as cursor:
        for index_name in indexes_to_remove:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name=?
            """, [index_name])
            if cursor.fetchone():
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                except Exception:
                    pass


def add_new_indexes_safely(apps, schema_editor):
    """Safely add new indexes if they don't exist."""
    indexes_to_add = [
        ('volunteer_app_activity', 'volunteer_a_act_datetime_idx', ['datetime']),
        ('volunteer_app_activity', 'volunteer_a_act_status_idx', ['status']),
        ('volunteer_app_user', 'volunteer_a_user_email_idx', ['email']),
        ('volunteer_app_qrscan', 'volunteer_a_qr_scanned_idx', ['scanned_at']),
        ('volunteer_app_activitysignup', 'volunteer_a_signup_status_idx', ['status']),
    ]
    
    with schema_editor.connection.cursor() as cursor:
        for table_name, index_name, fields in indexes_to_add:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name=?
            """, [index_name])
            if not cursor.fetchone():
                # Index doesn't exist, create it
                fields_str = ', '.join(fields)
                try:
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name} ({fields_str})
                    """)
                except Exception:
                    pass
    
    # Special handling for email_verified index (field may not exist)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='volunteer_a_user_email_v_idx'
        """)
        if not cursor.fetchone():
            # Check if email_verified column exists
            cursor.execute("""
                SELECT name FROM pragma_table_info('volunteer_app_user') 
                WHERE name='email_verified'
            """)
            if cursor.fetchone():
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS volunteer_a_user_email_v_idx 
                        ON volunteer_app_user (email_verified)
                    """)
                except Exception:
                    pass
    
    # Special handling for emailverification indexes (table may not exist)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='volunteer_app_emailverification'
        """)
        if cursor.fetchone():
            for index_name, field in [
                ('volunteer_a_email_token_idx', 'token'),
                ('volunteer_a_email_expires_idx', 'expires_at'),
            ]:
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name='{index_name}'
                """)
                if not cursor.fetchone():
                    try:
                        cursor.execute(f"""
                            CREATE INDEX IF NOT EXISTS {index_name} 
                            ON volunteer_app_emailverification ({field})
                        """)
                    except Exception:
                        pass


def reverse_operations(apps, schema_editor):
    """Reverse operation - not implemented."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('volunteer_app', '0008_email_verification'),
    ]

    operations = [
        migrations.RunPython(remove_old_indexes_safely, reverse_operations),
        migrations.RunPython(add_new_indexes_safely, reverse_operations),
    ]


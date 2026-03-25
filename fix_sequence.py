from django.db import connection

def fix_all_sequences():
    with connection.cursor() as cursor:
        print("جاري البحث عن كافة الجداول لإعادة ضبط التسلسل (Sequences)...")
        # الحصول على قائمة بكافة الجداول التي تحتوي على تسلسل
        cursor.execute("""
            SELECT t.relname, a.attname, s.relname as seqname
            FROM pg_class s
            JOIN pg_depend d ON d.objid = s.oid
            JOIN pg_class t ON t.oid = d.refobjid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
            WHERE s.relkind = 'S' AND t.relkind = 'r'
        """)
        sequences = cursor.fetchall()

        for table, column, seq in sequences:
            try:
                cursor.execute(f"SELECT MAX({column}) FROM {table}")
                max_id = cursor.fetchone()[0]
                if max_id:
                    cursor.execute(f"SELECT setval('{seq}', {max_id})")
                    print(f"تم تحديث {seq} للجدول {table} إلى: {max_id}")
                else:
                    cursor.execute(f"SELECT setval('{seq}', 1, false)")
                    print(f"إعادة ضبط {seq} للجدول {table} (جدول فارغ)")
            except Exception as e:
                print(f"فشل تحديث {table}: {e}")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_portal_backend.settings')
    django.setup()
    fix_all_sequences()
    print("\nتم الانتهاء من إصلاح كافة عدادات قاعدة البيانات بنجاح.")

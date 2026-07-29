from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0005_testcase_covered_risks'),
        ('incidents', '0005_incident_test_case'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='incident',
            name='test_case',
        ),
    ]

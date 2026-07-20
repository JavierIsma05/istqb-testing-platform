# Restores the optional risk-to-test-case traceability required by RF-03.5.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0004_testcase_steps_data_testcase_test_data_and_more'),
        ('incidents', '0004_remove_incident_test_case'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='test_case',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='risks',
                to='testcases.testcase',
            ),
        ),
    ]

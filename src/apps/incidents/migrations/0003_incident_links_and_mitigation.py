from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0002_requirement_requirement_type_and_more'),
        ('testcases', '0003_alter_testcase_status'),
        ('testplans', '0002_testplan_description_testplan_end_date_and_more'),
        ('incidents', '0002_incident_code_incident_impact_incident_probability_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='mitigation_strategy',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='incident',
            name='requirement',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='risks', to='requirements.requirement'),
        ),
        migrations.AddField(
            model_name='incident',
            name='test_case',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='risks', to='testcases.testcase'),
        ),
        migrations.AddField(
            model_name='incident',
            name='test_plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='risks', to='testplans.testplan'),
        ),
    ]

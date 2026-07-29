from django.db import migrations, models


def copy_legacy_risk_links(apps, schema_editor):
    Incident = apps.get_model('incidents', 'Incident')
    TestCase = apps.get_model('testcases', 'TestCase')

    for risk in Incident.objects.exclude(test_case_id__isnull=True):
        try:
            test_case = TestCase.objects.get(pk=risk.test_case_id)
        except TestCase.DoesNotExist:
            continue
        test_case.covered_risks.add(risk)


def reverse_legacy_risk_links(apps, schema_editor):
    Incident = apps.get_model('incidents', 'Incident')
    TestCase = apps.get_model('testcases', 'TestCase')

    for test_case in TestCase.objects.prefetch_related('covered_risks'):
        for risk in test_case.covered_risks.all():
            Incident.objects.filter(pk=risk.pk, test_case_id__isnull=True).update(test_case_id=test_case.pk)


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0005_incident_test_case'),
        ('testcases', '0004_testcase_steps_data_testcase_test_data_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcase',
            name='covered_risks',
            field=models.ManyToManyField(
                blank=True,
                related_name='covering_test_cases',
                to='incidents.incident',
            ),
        ),
        migrations.RunPython(copy_legacy_risk_links, reverse_legacy_risk_links),
    ]

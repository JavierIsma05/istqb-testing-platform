from django.db import migrations


def forward(apps, schema_editor):
    Defect = apps.get_model('defects', 'Defect')
    DefectHistory = apps.get_model('defects', 'DefectHistory')

    SEVERITY_MAP = {
        'CRITICAL': 'HIGH',
    }
    STATUS_MAP = {
        'ANALYSIS': 'IN_PROGRESS',
        'PENDING_CONFIRMATION': 'RESOLVED',
        'REJECTED': 'CLOSED',
        'DUPLICATED': 'CLOSED',
    }

    for defect in Defect.objects.all().iterator():
        changed = False
        if defect.severity in SEVERITY_MAP:
            defect.severity = SEVERITY_MAP[defect.severity]
            changed = True
        if defect.status in STATUS_MAP:
            defect.status = STATUS_MAP[defect.status]
            changed = True
        if defect.test_case_id is None and defect.execution_id is not None:
            defect.test_case_id = defect.execution.test_case_id
            changed = True
        if changed:
            defect.save()

    for history in DefectHistory.objects.all().iterator():
        changed = False
        if history.severity in SEVERITY_MAP:
            history.severity = SEVERITY_MAP[history.severity]
            changed = True
        if history.status in STATUS_MAP:
            history.status = STATUS_MAP[history.status]
            changed = True
        snapshot = history.snapshot or {}
        snapshot = dict(snapshot)
        if snapshot.get('severity') in SEVERITY_MAP:
            snapshot['severity'] = SEVERITY_MAP[snapshot['severity']]
            changed = True
        if snapshot.get('status') in STATUS_MAP:
            snapshot['status'] = STATUS_MAP[snapshot['status']]
            changed = True
        if snapshot.get('test_case_id') is None and history.defect_id is not None:
            defect = Defect.objects.filter(pk=history.defect_id).first()
            if defect:
                snapshot['test_case_id'] = defect.test_case_id
                changed = True
        if changed:
            history.snapshot = snapshot
            history.save()


class Migration(migrations.Migration):

    dependencies = [
        ('defects', '0006_defect_test_case_alter_defect_severity_and_more'),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]

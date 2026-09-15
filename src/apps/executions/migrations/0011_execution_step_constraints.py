from collections import defaultdict

from django.db import migrations, models


def normalize_duplicate_steps(apps, schema_editor):
    TestStepExecution = apps.get_model('executions', 'TestStepExecution')
    AutomatedValidationRule = apps.get_model('executions', 'AutomatedValidationRule')

    for model, group_fields in (
        (TestStepExecution, ('test_execution_id', 'step_number')),
        (AutomatedValidationRule, ('test_case_id', 'step_number')),
    ):
        seen = defaultdict(list)
        for row in model.objects.order_by('id').values('id', *group_fields):
            seen[tuple(row[field] for field in group_fields)].append(row['id'])

        for (_, _), ids in seen.items():
            if len(ids) <= 1:
                continue
            used = set(
                model.objects.filter(**{group_fields[0]: model.objects.filter(pk=ids[0]).values_list(group_fields[0], flat=True).first()})
                .values_list('step_number', flat=True)
            )
            next_number = max(used or {0}) + 1
            for duplicate_id in ids[1:]:
                while next_number in used:
                    next_number += 1
                model.objects.filter(pk=duplicate_id).update(step_number=next_number)
                used.add(next_number)
                next_number += 1


class Migration(migrations.Migration):

    dependencies = [
        ('executions', '0010_testexecution_approval_percentage'),
    ]

    operations = [
        migrations.RunPython(normalize_duplicate_steps, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='teststepexecution',
            constraint=models.UniqueConstraint(
                fields=('test_execution', 'step_number'),
                name='uniq_step_execution_number',
            ),
        ),
        migrations.AddConstraint(
            model_name='automatedvalidationrule',
            constraint=models.UniqueConstraint(
                fields=('test_case', 'step_number'),
                name='uniq_automated_rule_step_number',
            ),
        ),
    ]

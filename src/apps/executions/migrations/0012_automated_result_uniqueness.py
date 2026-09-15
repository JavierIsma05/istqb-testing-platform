from django.db import migrations, models


def reconcile_duplicate_automated_results(apps, schema_editor):
    AutomatedExecutionResult = apps.get_model('executions', 'AutomatedExecutionResult')
    seen = set()
    for row in AutomatedExecutionResult.objects.order_by('test_execution_id', 'validation_rule_id', '-id').values(
        'id', 'test_execution_id', 'validation_rule_id'
    ):
        key = (row['test_execution_id'], row['validation_rule_id'])
        if key in seen:
            AutomatedExecutionResult.objects.filter(pk=row['id']).delete()
        else:
            seen.add(key)


class Migration(migrations.Migration):

    dependencies = [
        ('executions', '0011_execution_step_constraints'),
    ]

    operations = [
        migrations.RunPython(reconcile_duplicate_automated_results, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='automatedexecutionresult',
            constraint=models.UniqueConstraint(
                fields=('test_execution', 'validation_rule'),
                name='uniq_automated_result_rule_execution',
            ),
        ),
    ]

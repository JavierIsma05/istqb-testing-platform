from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('executions', '0010_testexecution_approval_percentage'),
    ]

    operations = [
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

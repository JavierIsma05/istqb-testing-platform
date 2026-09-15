from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('executions', '0011_execution_step_constraints'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='automatedexecutionresult',
            constraint=models.UniqueConstraint(
                fields=('test_execution', 'validation_rule'),
                name='uniq_automated_result_rule_execution',
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('executions', '0009_automatedexecutionresult_comparison_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='testexecution',
            name='approval_percentage',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]

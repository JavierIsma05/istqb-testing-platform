from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('testcases', '0008_testcase_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcase',
            name='reexecution_requested',
            field=models.BooleanField(
                default=False,
                help_text='Indica que el caso fue reabierto explícitamente desde la matriz para una nueva ejecución.',
            ),
        ),
    ]

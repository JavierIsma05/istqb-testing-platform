from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('executions', '0013_alter_teststepexecution_expected_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='testexecution',
            name='script_generado',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='testexecution',
            name='salida_consola',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='testexecution',
            name='errores',
            field=models.TextField(blank=True),
        ),
    ]

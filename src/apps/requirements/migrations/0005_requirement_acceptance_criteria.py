from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('requirements', '0004_alter_requirement_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='requirement',
            name='acceptance_criteria',
            field=models.TextField(
                blank=True,
                help_text='Condiciones verificables que deben cumplirse para aceptar el requisito.',
            ),
        ),
        migrations.AddField(
            model_name='requirementversion',
            name='acceptance_criteria',
            field=models.TextField(blank=True),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('defects', '0008_defect_lifecycle_controls'),
    ]

    operations = [
        migrations.AlterField(
            model_name='defect',
            name='status',
            field=models.CharField(
                choices=[
                    ('OPEN', 'Abierto'),
                    ('ANALYSIS', 'En análisis'),
                    ('IN_PROGRESS', 'En progreso'),
                    ('RESOLVED', 'Resuelto'),
                    ('PENDING_CONFIRMATION', 'Pendiente de confirmación'),
                    ('CLOSED', 'Cerrado'),
                    ('REOPENED', 'Reabierto'),
                    ('REJECTED', 'Rechazado'),
                    ('DUPLICATED', 'Duplicado'),
                ],
                default='OPEN',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='defecthistory',
            name='status',
            field=models.CharField(
                choices=[
                    ('OPEN', 'Abierto'),
                    ('ANALYSIS', 'En análisis'),
                    ('IN_PROGRESS', 'En progreso'),
                    ('RESOLVED', 'Resuelto'),
                    ('PENDING_CONFIRMATION', 'Pendiente de confirmación'),
                    ('CLOSED', 'Cerrado'),
                    ('REOPENED', 'Reabierto'),
                    ('REJECTED', 'Rechazado'),
                    ('DUPLICATED', 'Duplicado'),
                ],
                max_length=30,
            ),
        ),
    ]

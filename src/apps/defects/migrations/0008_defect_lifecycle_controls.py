from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('defects', '0007_migrate_defect_severity_status_test_case'),
        ('executions', '0010_testexecution_approval_percentage'),
    ]

    operations = [
        migrations.AddField(
            model_name='defect',
            name='resolution',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='defect',
            name='verification_execution',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='verified_defects',
                to='executions.testexecution',
            ),
        ),
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
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('testcases', '0007_testcase_custom_technique_alter_testcase_technique'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TestCaseVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.PositiveIntegerField(default=1)),
                ('version_label', models.CharField(default='1.0', max_length=20)),
                ('title', models.CharField(max_length=180)),
                ('status', models.CharField(choices=[('PENDING', 'En Redacción'), ('READY', 'Listo para Ejecutar'), ('RUNNING', 'Ejecutando'), ('PASSED', 'Completado'), ('FAILED', 'Fallido'), ('BLOCKED', 'Bloqueado')], max_length=20)),
                ('change_reason', models.CharField(blank=True, max_length=180)),
                ('snapshot', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('test_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='testcases.testcase')),
            ],
            options={
                'ordering': ['test_case', '-version_number'],
                'unique_together': {('test_case', 'version_number')},
            },
        ),
    ]

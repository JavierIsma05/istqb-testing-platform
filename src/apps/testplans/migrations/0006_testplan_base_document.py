# Generated manually to preserve the incremental plan-document feature.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testplans', '0005_testplan_maximum_critical_defects_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='testplan',
            name='base_document',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='test_plan_documents/%Y/%m/',
                validators=[django.core.validators.FileExtensionValidator(
                    allowed_extensions=['pdf', 'docx', 'xlsx', 'odt', 'txt'],
                )],
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testplans', '0002_testplan_description_testplan_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='testplan',
            name='environment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='testplan',
            name='estimation',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='testplan',
            name='responsibilities',
            field=models.TextField(blank=True),
        ),
    ]

from django.db import migrations, models


def ensure_void_reason_column(apps, schema_editor):
    TestExecution = apps.get_model('executions', 'TestExecution')
    table_name = TestExecution._meta.db_table
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }
    if 'void_reason' not in existing_columns:
        field = models.CharField(max_length=500, blank=True, default='')
        field.set_attributes_from_name('void_reason')
        field.model = TestExecution
        schema_editor.add_field(TestExecution, field)


class Migration(migrations.Migration):
    dependencies = [
        ('executions', '0015_testexecution_is_voided'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(ensure_void_reason_column, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='testexecution',
                    name='void_reason',
                    field=models.CharField(blank=True, default='', max_length=500),
                ),
            ],
        ),
    ]

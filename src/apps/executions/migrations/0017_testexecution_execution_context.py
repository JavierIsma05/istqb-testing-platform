from django.db import migrations, models


def ensure_execution_context_column(apps, schema_editor):
    TestExecution = apps.get_model('executions', 'TestExecution')
    table_name = TestExecution._meta.db_table
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }
    if 'execution_context' not in existing_columns:
        field = models.CharField(max_length=500, blank=True, default='')
        field.set_attributes_from_name('execution_context')
        field.model = TestExecution
        schema_editor.add_field(TestExecution, field)


class Migration(migrations.Migration):
    dependencies = [
        ('executions', '0016_testexecution_void_reason'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(ensure_execution_context_column, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='testexecution',
                    name='execution_context',
                    field=models.CharField(blank=True, default='', max_length=500),
                ),
            ],
        ),
    ]

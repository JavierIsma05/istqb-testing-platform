from django.db import migrations, models


def ensure_is_voided_column(apps, schema_editor):
    TestExecution = apps.get_model('executions', 'TestExecution')
    table_name = TestExecution._meta.db_table
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }
    if 'is_voided' not in existing_columns:
        field = models.BooleanField(default=False)
        field.set_attributes_from_name('is_voided')
        field.model = TestExecution
        schema_editor.add_field(TestExecution, field)


class Migration(migrations.Migration):
    dependencies = [
        ('executions', '0014_testexecution_automation_audit'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(ensure_is_voided_column, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='testexecution',
                    name='is_voided',
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]

from django.db import migrations


LEGACY_COLUMNS = (
    "uses_risk_management",
    "entry_criteria_items",
    "exit_criteria_items",
)


def remove_legacy_columns(apps, schema_editor):
    """Remove obsolete TestPlan columns on every supported database backend."""
    connection = schema_editor.connection
    quote = connection.ops.quote_name
    table_name = "testplans_testplan"
    table = quote(table_name)

    # Django's introspection API is backend-agnostic. The previous implementation
    # queried PostgreSQL's information_schema directly, which made the migration
    # fail when the test suite used SQLite.
    with connection.cursor() as cursor:
        existing = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, table_name
            )
        }

        for column in LEGACY_COLUMNS:
            if column in existing:
                cursor.execute(
                    f"ALTER TABLE {table} DROP COLUMN {quote(column)}"
                )


class Migration(migrations.Migration):
    dependencies = [
        ("testplans", "0007_remove_testplan_base_document"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_columns, migrations.RunPython.noop),
    ]

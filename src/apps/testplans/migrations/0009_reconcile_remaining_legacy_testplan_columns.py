from django.db import migrations


LEGACY_COLUMNS = (
    "exit_criteria_items",
)


def remove_remaining_legacy_columns(apps, schema_editor):
    """Remove obsolete TestPlan columns on every supported database backend."""
    connection = schema_editor.connection
    quote = connection.ops.quote_name
    table_name = "testplans_testplan"
    table = quote(table_name)

    # Use Django's backend-agnostic introspection so SQLite test databases and
    # PostgreSQL production databases execute the same migration safely.
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
        ("testplans", "0008_reconcile_legacy_testplan_columns"),
    ]

    operations = [
        migrations.RunPython(
            remove_remaining_legacy_columns,
            migrations.RunPython.noop,
        ),
    ]

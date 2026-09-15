from django.db import migrations


LEGACY_COLUMNS = (
    "uses_risk_management",
    "entry_criteria_items",
    "exit_criteria_items",
)


def remove_legacy_columns(apps, schema_editor):
    """Remove columns left by obsolete TestPlan schemas on every supported DB."""
    connection = schema_editor.connection
    quote = connection.ops.quote_name
    table_name = "testplans_testplan"
    table = quote(table_name)

    # Use Django's backend-agnostic introspection instead of PostgreSQL-only
    # information_schema queries. This keeps the migration executable with the
    # SQLite database used by the test suite as well as PostgreSQL in production.
    existing = {
        column.name
        for column in connection.introspection.get_table_description(
            connection.cursor(), table_name
        )
    }

    for column in LEGACY_COLUMNS:
        if column in existing:
            with connection.schema_editor() as editor:
                editor.execute(
                    f"ALTER TABLE {table} DROP COLUMN {quote(column)}"
                )


class Migration(migrations.Migration):
    dependencies = [
        ("testplans", "0007_remove_testplan_base_document"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_columns, migrations.RunPython.noop),
    ]

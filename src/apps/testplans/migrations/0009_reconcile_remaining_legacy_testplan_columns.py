from django.db import migrations


LEGACY_COLUMNS = (
    "exit_criteria_items",
)


def remove_remaining_legacy_columns(apps, schema_editor):
    """Remove obsolete TestPlan columns from databases that missed 0008."""
    connection = schema_editor.connection
    quote = connection.ops.quote_name
    table = quote("testplans_testplan")

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name "
            "FROM information_schema.columns "
            "WHERE table_schema = current_schema() "
            "AND table_name = %s",
            ["testplans_testplan"],
        )
        existing = {row[0] for row in cursor.fetchall()}
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

from django.db import migrations


LEGACY_COLUMNS = (
    "uses_risk_management",
    "entry_criteria_items",
    "exit_criteria_items",
)


def remove_legacy_columns(apps, schema_editor):
    """Remove columns left by obsolete TestPlan schemas.

    The current TestPlan model and migrations do not define these columns.
    The operation is conditional so it is safe for clean databases and for
    databases where one or more legacy columns were already removed.
    """
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
        ("testplans", "0007_remove_testplan_base_document"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_columns, migrations.RunPython.noop),
    ]

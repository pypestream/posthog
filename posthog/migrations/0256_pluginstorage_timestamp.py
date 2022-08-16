# Generated by Django 3.2.14 on 2022-08-16 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("posthog", "0255_user_prompt_sequence_state"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="pluginstorage", name="posthog_unique_plugin_storage_key",),
        migrations.AddField(
            model_name="pluginstorage", name="timestamp", field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS pluginstorage_timestamp_date_idx ON posthog_pluginstorage(timestamp);",
            reverse_sql="DROP INDEX IF EXISTS pluginstorage_timestamp_date_idx;",
        ),
    ]

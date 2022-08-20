# Generated by Django 3.2.14 on 2022-08-20 16:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0256_add_async_deletion_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dashboardtile",
            name="dashboard",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="dashboard_tiles", to="posthog.dashboard"
            ),
        ),
        migrations.AlterField(
            model_name="dashboardtile",
            name="insight",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="dashboard_tiles", to="posthog.insight"
            ),
        ),
    ]

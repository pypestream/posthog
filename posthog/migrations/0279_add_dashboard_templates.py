# Generated by Django 3.2.15 on 2022-11-14 16:11

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models

import posthog.models.utils
from posthog.helpers.dashboard_templates import create_default_global_templates


def create_dashboard_templates(apps, _):
    create_default_global_templates()


def remove_dashboard_templates(apps, _):
    # no need to do anything here as the CreateModel reversal removes the table
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0278_organization_customer_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="DashboardTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=posthog.models.utils.UUIDT, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "scope",
                    models.CharField(
                        choices=[("project", "project"), ("organization", "organization"), ("global", "global")],
                        default="project",
                        max_length=24,
                    ),
                ),
                ("template_name", models.CharField(max_length=400, null=True)),
                ("source_dashboard", models.IntegerField(null=True)),
                ("dashboard_description", models.CharField(max_length=400, null=True)),
                ("dashboard_filters", models.JSONField(null=True)),
                ("tiles", models.JSONField(default=list)),
                (
                    "tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=255), default=list, size=None
                    ),
                ),
                ("deleted", models.BooleanField(default=False)),
                (
                    "organization",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.CASCADE, to="posthog.organization"
                    ),
                ),
                ("team", models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="posthog.team")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.RunPython(create_dashboard_templates, remove_dashboard_templates),
    ]

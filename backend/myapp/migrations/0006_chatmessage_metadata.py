# Generated by Django 5.1.3 on 2025-01-08 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0005_remove_chatsession_last_used_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="metadata",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
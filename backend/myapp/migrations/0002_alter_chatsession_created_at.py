# Generated by Django 4.1.13 on 2024-08-14 16:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatsession",
            name="created_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
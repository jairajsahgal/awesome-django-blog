# Generated by Django 4.1.2 on 2023-01-28 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0027_bumpCharacterLimit"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
    ]

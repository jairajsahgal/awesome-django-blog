# Generated by Django 3.2.13 on 2022-05-30 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0015_add_ckeditor_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='metaimg_alt_txt',
            field=models.CharField(default='Meta Image', max_length=60),
        ),
    ]

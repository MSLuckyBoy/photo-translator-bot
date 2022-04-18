# Generated by Django 4.0.3 on 2022-04-04 09:42

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('botapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='time_create',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='message',
            name='time_update',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

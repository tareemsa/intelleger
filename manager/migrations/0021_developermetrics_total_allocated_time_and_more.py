# Generated by Django 5.0.3 on 2024-06-04 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0020_remove_task_developers_task_developer'),
    ]

    operations = [
        migrations.AddField(
            model_name='developermetrics',
            name='total_allocated_time',
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='developermetrics',
            name='total_delivery_time',
            field=models.DurationField(blank=True, null=True),
        ),
    ]

# Generated by Django 5.0.3 on 2024-05-22 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0009_remove_task_ai_requirements_project_ai_requirements'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]

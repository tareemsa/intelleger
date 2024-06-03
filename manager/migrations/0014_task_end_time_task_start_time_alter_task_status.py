# Generated by Django 5.0.3 on 2024-06-02 21:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0013_remove_project_ai_requirements_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='start_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='not_started', max_length=50),
        ),
    ]

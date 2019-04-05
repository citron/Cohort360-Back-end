# Generated by Django 2.1.7 on 2019-04-05 14:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField(blank=True)),
                ('shared', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Exploration',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField(blank=True)),
                ('favorite', models.BooleanField(default=False)),
                ('shared', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.TextField(blank=True)),
                ('shared', models.BooleanField(default=False)),
                ('stats_number_of_patients', models.BigIntegerField(default=0)),
                ('stats_number_of_documents', models.BigIntegerField(default=0)),
                ('refresh_every', models.BigIntegerField(default=0)),
                ('refresh_new_number_of_patients', models.BigIntegerField(default=0)),
                ('exploration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='explorations.Exploration')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='cohort',
            name='request',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='explorations.Request'),
        ),
    ]

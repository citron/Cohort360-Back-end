# Generated by Django 3.2.5 on 2021-11-08 18:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('explorations', '0010_auto_20211102_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='cohortresult',
            name='dated_measure_global',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='restricted_cohort', to='explorations.datedmeasure'),
        ),
        migrations.AddField(
            model_name='datedmeasure',
            name='measure_max',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='datedmeasure',
            name='measure_min',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='datedmeasure',
            name='mode',
            field=models.CharField(choices=[('Snapshot', 'Snapshot'), ('Global', 'Global')], default='Snapshot', max_length=20, null=True),
        ),
    ]

# Generated by Django 5.1.2 on 2024-11-01 09:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_sensortype_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='measurement',
            name='sensor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='measurements', to='core.sensor'),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sensors', to='core.location'),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='sensor_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sensors', to='core.sensortype'),
        ),
    ]
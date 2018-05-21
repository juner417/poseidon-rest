# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-22 11:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clusters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(default='comp-05a781d0', max_length=20, unique=True)),
                ('name', models.CharField(max_length=30)),
                ('role', models.CharField(max_length=30)),
                ('opts', jsonfield.fields.JSONField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clusters.Cluster', to_field='uuid')),
            ],
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-22 11:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clusters', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cluster',
            name='uuid',
            field=models.CharField(default='cluster-bca95a7e', max_length=20, unique=True),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-02 04:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0003_auto_20170223_1841'),
    ]

    operations = [
        migrations.RenameField(
            model_name='node',
            old_name='role',
            new_name='roles',
        ),
    ]

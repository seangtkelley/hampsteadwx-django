# Generated by Django 3.0.5 on 2020-05-24 00:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20200524_0020'),
    ]

    operations = [
        migrations.AddField(
            model_name='snowseason',
            name='total',
            field=models.DecimalField(decimal_places=1, default=18.3, max_digits=8),
            preserve_default=False,
        ),
    ]

# Generated by Django 3.0.5 on 2020-05-26 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='annualsummary',
            name='year',
            field=models.IntegerField(default=2019),
            preserve_default=False,
        ),
    ]

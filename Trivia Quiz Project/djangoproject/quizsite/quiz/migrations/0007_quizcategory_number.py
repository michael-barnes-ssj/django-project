# Generated by Django 2.0.3 on 2018-06-14 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0006_auto_20180614_2020'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizcategory',
            name='number',
            field=models.IntegerField(null=True),
        ),
    ]

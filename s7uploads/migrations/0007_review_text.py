# Generated by Django 2.1.3 on 2018-12-29 02:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('s7uploads', '0006_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='text',
            field=models.CharField(default='', max_length=2048),
            preserve_default=False,
        ),
    ]

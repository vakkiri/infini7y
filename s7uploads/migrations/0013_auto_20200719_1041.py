# Generated by Django 2.2.12 on 2020-07-19 15:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('s7uploads', '0012_auto_20200718_1250'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='UploadVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField()),
                ('version_notes', models.TextField()),
                ('version_name', models.CharField(max_length=10)),
                ('num_downloads', models.IntegerField()),
                ('file_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='s7uploads.File')),
            ],
        ),
        migrations.RemoveField(
            model_name='upload',
            name='uploadDate',
        ),
        migrations.RemoveField(
            model_name='upload',
            name='versionNotes',
        ),
        migrations.RemoveField(
            model_name='upload',
            name='versionNumber',
        ),
        migrations.RemoveField(
            model_name='upload',
            name='version_downloads',
        ),
        migrations.AlterField(
            model_name='review',
            name='upload',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='s7uploads.UploadVersion'),
        ),
        migrations.AddField(
            model_name='uploadversion',
            name='upload_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='s7uploads.Upload'),
        ),
    ]

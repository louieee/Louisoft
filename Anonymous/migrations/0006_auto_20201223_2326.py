# Generated by Django 3.0.6 on 2020-12-23 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Anonymous', '0005_auto_20201223_2215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='secret',
            field=models.BinaryField(default=b'4MhmDlzh1PcaXPfeR9ALdquvLaytN2EZm4q_a0bA8IY='),
        ),
        migrations.AlterField(
            model_name='consultant',
            name='code',
            field=models.CharField(default='Consult-pKmAGYFKyHdqEA23', max_length=32),
        ),
        migrations.AlterField(
            model_name='message',
            name='image',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='None/message/images'),
        ),
        migrations.AlterField(
            model_name='message',
            name='send_status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'NOT_SENT'), (1, 'SENT'), (2, 'DELIVERED')], default=0),
        ),
    ]

# Generated by Django 3.0.6 on 2020-12-23 21:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Anonymous', '0003_auto_20201102_1552'),
    ]

    operations = [
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Anonymous', max_length=30)),
                ('text', models.TextField(default=None)),
                ('date_added', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterField(
            model_name='chat',
            name='secret',
            field=models.BinaryField(default=b'JistVSWbuaD8NWinQrEjrw5ORk4euYn31UNykfyU_Hs='),
        ),
        migrations.AlterField(
            model_name='consultant',
            name='code',
            field=models.CharField(default='Consult-CjA_x5nZN7RXOWS0', max_length=16),
        ),
        migrations.AlterField(
            model_name='order',
            name='orders',
            field=models.TextField(default='{}'),
        ),
        migrations.DeleteModel(
            name='Testimony',
        ),
        migrations.AddField(
            model_name='testimonial',
            name='order',
            field=models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Anonymous.Order'),
        ),
    ]

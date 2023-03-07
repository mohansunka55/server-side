# Generated by Django 4.1.3 on 2023-03-06 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('phone_number', models.BigIntegerField(unique=True, verbose_name='Phone Number')),
                ('employee_id', models.CharField(max_length=255, unique=True)),
                ('email', models.EmailField(blank=True, max_length=255, null=True, unique=True, verbose_name='Email Address')),
                ('is_approved', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_customer', models.BooleanField(default=False)),
                ('is_store_manager', models.BooleanField(default=False)),
                ('is_sales_and_marketing', models.BooleanField(default=False)),
                ('is_service', models.BooleanField(default=False)),
                ('is_analytics', models.BooleanField(default=False)),
                ('slug', models.SlugField(blank=True, max_length=250, null=True, unique=True)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies = [('social', '0011_brandidea'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='MetaSession', fields=[('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')), ('nonce', models.CharField(max_length=64, unique=True)), ('expires_at', models.DateTimeField()), ('used', models.BooleanField(default=False)), ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)), ('brand', models.ForeignKey(to='social.brand', on_delete=django.db.models.deletion.CASCADE))]),
        migrations.CreateModel(name='MetaConnection', fields=[('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')), ('platform', models.CharField(max_length=20)), ('remote_id', models.CharField(max_length=100)), ('name', models.CharField(max_length=255)), ('encrypted_token', models.TextField()), ('active', models.BooleanField(default=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('brand', models.ForeignKey(to='social.brand', on_delete=django.db.models.deletion.CASCADE))], options={'unique_together': {('brand', 'platform', 'remote_id')}}),
        migrations.CreateModel(name='MetaPublication', fields=[('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')), ('caption', models.TextField()), ('image_url', models.URLField(max_length=2000, blank=True)), ('status', models.CharField(max_length=20, default='sending')), ('remote_id', models.CharField(max_length=100, blank=True)), ('created_at', models.DateTimeField(auto_now_add=True)), ('request_id', models.UUIDField(unique=True)), ('connection', models.ForeignKey(to='social.metaconnection', on_delete=django.db.models.deletion.CASCADE))]),
    ]

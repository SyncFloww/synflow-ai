from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies = [('social', '0012_meta_connections'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='metaconnection', name='auto_reply', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='metaconnection', name='reply_enabled_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='metaconnection', name='last_checked_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='metaconnection', name='automation_user', field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True)),
        migrations.AddField(model_name='metapublication', name='scheduled_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='metapublication', name='requested_by', field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True)),
        migrations.CreateModel(name='MetaReply', fields=[('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')), ('comment_id', models.CharField(max_length=100)), ('comment_text', models.TextField(blank=True)), ('reply', models.TextField(blank=True)), ('status', models.CharField(max_length=20, default='pending')), ('remote_id', models.CharField(max_length=100, blank=True)), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('publication', models.ForeignKey(to='social.metapublication', on_delete=django.db.models.deletion.CASCADE))], options={'unique_together': {('publication', 'comment_id')}}),
        migrations.CreateModel(name='MetaWorkerLease', fields=[('name', models.CharField(max_length=50, primary_key=True, serialize=False)), ('expires_at', models.DateTimeField())]),
    ]

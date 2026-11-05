from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies = [('social', '0013_meta_automation')]
    operations = [
        migrations.AddField(model_name='metapublication', name='last_status_checked_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.CreateModel(name='InboxSend', fields=[('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')), ('conversation_id', models.CharField(max_length=255)), ('request_id', models.UUIDField(unique=True)), ('text', models.TextField()), ('status', models.CharField(max_length=20, default='sending')), ('remote_id', models.CharField(max_length=255, blank=True)), ('created_at', models.DateTimeField(auto_now_add=True)), ('connection', models.ForeignKey(to='social.metaconnection', on_delete=django.db.models.deletion.CASCADE))]),
        migrations.AddField(model_name='metaconnection', name='encrypted_refresh_token', field=models.TextField(blank=True)),
        migrations.AddField(model_name='metaconnection', name='token_expires_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='metaconnection', name='refresh_expires_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='metaconnection', name='scopes', field=models.JSONField(default=list, blank=True)),
        migrations.AddField(model_name='metapublication', name='video_url', field=models.URLField(max_length=2000, blank=True)),
        migrations.AddField(model_name='metapublication', name='post_options', field=models.JSONField(default=dict, blank=True)),
        migrations.AddField(model_name='metapublication', name='provider_publish_id', field=models.CharField(max_length=100, blank=True)),
    ]

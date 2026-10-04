from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('social', '0010_brandlead'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='BrandIdea', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('title', models.CharField(max_length=255)),
        ('hook', models.TextField()), ('angle', models.TextField()), ('cta', models.TextField()),
        ('platform', models.CharField(max_length=50, default='instagram')),
        ('approved_at', models.DateTimeField(null=True, blank=True)),
        ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
        ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ideas', to='social.brand')),
        ('approved_by', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
    ], options={'ordering': ['-updated_at', '-id']})]

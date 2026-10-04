from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('social', '0009_brandmessage'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='BrandLead', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('name', models.CharField(max_length=255)),
        ('email', models.EmailField(max_length=254)),
        ('source', models.CharField(max_length=255)),
        ('note', models.TextField(blank=True)),
        ('consent_at', models.DateTimeField()),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leads', to='social.brand')),
        ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
    ], options={'ordering': ['-created_at', '-id']})]

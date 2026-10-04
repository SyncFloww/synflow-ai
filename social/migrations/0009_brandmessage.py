from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('social', '0008_brand_interview'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='BrandMessage', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('role', models.CharField(max_length=10, choices=[('user', 'User'), ('assistant', 'Assistant')])),
        ('content', models.TextField()),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='social.brand')),
        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
    ], options={'ordering': ['created_at', 'id']})]

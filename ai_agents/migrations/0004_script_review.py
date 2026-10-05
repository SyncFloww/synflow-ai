from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('ai_agents', '0003_aicaption_aicontentproject_aijob_aiscript_and_more'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='aiscript', name='review_status', field=models.CharField(max_length=20, choices=[('DRAFT', 'Draft'), ('IN_REVIEW', 'In review'), ('APPROVED', 'Approved')], default='DRAFT')),
        migrations.AddField(model_name='aiscript', name='approved_at', field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name='aiscript', name='approved_by', field=models.ForeignKey(null=True, blank=True, related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
    ]

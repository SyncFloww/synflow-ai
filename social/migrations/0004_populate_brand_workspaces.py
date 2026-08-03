from django.db import migrations
from django.utils.text import slugify

def populate_brand_workspaces(apps, schema_editor):
    Brand = apps.get_model('social', 'Brand')
    Workspace = apps.get_model('workspaces', 'Workspace')
    WorkspaceMember = apps.get_model('workspaces', 'WorkspaceMember')
    BrandProfile = apps.get_model('social', 'BrandProfile')

    for brand in Brand.objects.all():
        if not brand.created_by and brand.user:
            brand.created_by = brand.user

        if not brand.workspace:
            if brand.user:
                ws = Workspace.objects.filter(owner=brand.user).first() or Workspace.objects.filter(members__user=brand.user).first()
                if not ws:
                    ws = Workspace.objects.create(
                        owner=brand.user,
                        created_by=brand.user,
                        name=f"{brand.user.username}'s Workspace",
                        slug=f"{brand.user.username}-workspace"
                    )
                    WorkspaceMember.objects.get_or_create(
                        workspace=ws,
                        user=brand.user,
                        defaults={'role': 'OWNER', 'status': 'ACTIVE'}
                    )
                brand.workspace = ws

        if not brand.slug:
            base_slug = slugify(brand.name) or "brand"
            slug = base_slug
            counter = 1
            while Brand.objects.filter(workspace=brand.workspace, slug=slug).exclude(id=brand.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            brand.slug = slug

        brand.save()

        if not hasattr(brand, 'profile') and not BrandProfile.objects.filter(brand=brand).exists():
            BrandProfile.objects.create(
                brand=brand,
                industry=brand.industry or '',
                brand_voice=brand.voice or '',
                target_audience=brand.target_audience or ''
            )

def rollback(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('social', '0003_brand_created_by_brand_industry_brand_slug_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_brand_workspaces, rollback),
    ]

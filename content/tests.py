import io
from django.urls import reverse
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from workspaces.models import Workspace
from accounts.models import User
from .models import Content, ContentVersion, MediaAsset

class ContentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="StrongPass123!", first_name="Test", last_name="User")
        self.workspace = Workspace.objects.create(name="Test Workspace", slug="test-workspace", owner=self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_content(self):
        url = reverse('content-list', kwargs={'workspace_id': self.workspace.id})
        data = {
            "title": "My first post",
            "text_content": "Hello world!"
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "My first post")
        
        # Verify initial version is created
        content_id = response.data["id"]
        versions = ContentVersion.objects.filter(content_id=content_id)
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().text_content, "Hello world!")

    def test_edit_content_creates_version(self):
        content = Content.objects.create(
            workspace=self.workspace,
            author=self.user,
            title="Original",
            text_content="Original text"
        )
        # Create the initial version manually since we didn't go through the view
        ContentVersion.objects.create(content=content, text_content="Original text", edited_by=self.user)
        
        url = reverse('content-detail', kwargs={'workspace_id': self.workspace.id, 'pk': content.id})
        data = {
            "title": "Updated",
            "text_content": "Updated text"
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        
        versions = ContentVersion.objects.filter(content=content).order_by('-created_at')
        self.assertEqual(versions.count(), 2)
        self.assertEqual(versions[0].text_content, "Updated text")
        self.assertEqual(versions[1].text_content, "Original text")

    def test_upload_and_attach_media(self):
        # 1. Upload Media
        url_media = reverse('media-list', kwargs={'workspace_id': self.workspace.id})
        image_content = b"fake_image_data"
        image = SimpleUploadedFile("test_image.jpg", image_content, content_type="image/jpeg")
        
        response = self.client.post(url_media, {"file": image}, format="multipart")
        self.assertEqual(response.status_code, 201)
        
        media_id = response.data["id"]
        media = MediaAsset.objects.get(id=media_id)
        self.assertEqual(media.file_type, "image/jpeg")
        
        # 2. Attach Media
        content = Content.objects.create(
            workspace=self.workspace,
            author=self.user,
            title="Post with Media",
            text_content="Check out this image!"
        )
        
        url_attach = reverse('content-attach-media', kwargs={'workspace_id': self.workspace.id, 'pk': content.id})
        response = self.client.post(url_attach, {"media_id": media_id}, format='json')
        self.assertEqual(response.status_code, 200)
        
        content.refresh_from_db()
        self.assertIn(media, content.media_assets.all())

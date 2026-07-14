from django.contrib import admin
from .models import Workspace, WorkspaceMember, Invitation, WorkspaceSetting

admin.site.register((Workspace, WorkspaceMember, Invitation, WorkspaceSetting))

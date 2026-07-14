from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from workspaces.models import Workspace
from workspaces.permissions import member_for, can_manage
from .models import Brand
from .serializers import BrandSerializer


class BrandListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        if not member_for(request.user, workspace):
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(BrandSerializer(workspace.brands.select_related("voice"), many=True).data)

    def post(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        if not can_manage(member_for(request.user, workspace)):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = BrandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(BrandSerializer(serializer.save(workspace=workspace)).data, status=status.HTTP_201_CREATED)


class BrandDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_brand(self, request, workspace_id, pk):
        workspace = get_object_or_404(Workspace, pk=workspace_id)
        if not member_for(request.user, workspace):
            return None
        return get_object_or_404(Brand.objects.select_related("voice"), workspace=workspace, pk=pk)

    def get(self, request, workspace_id, pk):
        brand = self.get_brand(request, workspace_id, pk)
        return Response(BrandSerializer(brand).data) if brand else Response(status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, workspace_id, pk):
        brand = self.get_brand(request, workspace_id, pk)
        if not brand or not can_manage(member_for(request.user, brand.workspace)):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = BrandSerializer(brand, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(BrandSerializer(serializer.save()).data)

    def delete(self, request, workspace_id, pk):
        brand = self.get_brand(request, workspace_id, pk)
        if not brand or not can_manage(member_for(request.user, brand.workspace)):
            return Response(status=status.HTTP_403_FORBIDDEN)
        brand.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

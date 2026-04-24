from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from reports.models import DCC, Institution, InstitutionPhoto
from reports.views import generate_institution_pdf, generate_dcc_excel
from .serializers import DCCSerializer, InstitutionSerializer, InstitutionPhotoSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class DCCViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DCC.objects.all()
    serializer_class = DCCSerializer

    @swagger_auto_schema(
        operation_description="Generate Excel report (two sheets) for a DCC.",
        responses={200: openapi.Response('Excel file', schema=openapi.Schema(type=openapi.TYPE_FILE))}
    )

    @action(detail=True, methods=['get'])
    def excel_report(self, request, pk=None):
        """Download Excel report for this DCC"""
        return generate_dcc_excel(request, pk)

class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer

    @swagger_auto_schema(
        operation_description="Download PDF report for an institution.",
        responses={200: openapi.Response('PDF file', schema=openapi.Schema(type=openapi.TYPE_FILE))}
    )

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Download PDF for this institution"""
        return generate_institution_pdf(request, pk)
    
    @swagger_auto_schema(
        operation_description="Upload a before/after installation photo for a specific device.",
        manual_parameters=[
            openapi.Parameter('photo_type', openapi.IN_FORM, description="'before' or 'after'", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('device_type', openapi.IN_FORM, description="ONU/AP1/AP2/AP3/OUT", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('image', openapi.IN_FORM, description="Image file", type=openapi.TYPE_FILE, required=True),
        ],
        responses={201: InstitutionPhotoSerializer, 400: 'Bad Request'}
    )

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_photos(self, request, pk=None):
        """Upload before/after photos for a specific device"""
        institution = self.get_object()
        photo_type = request.data.get('photo_type')  # 'before' or 'after'
        device_type = request.data.get('device_type') # ONU/AP1/AP2/AP3/OUT
        image_file = request.FILES.get('image')

        if not all([photo_type, device_type, image_file]):
            return Response({'error': 'Missing required fields'}, status=400)

        photo, created = InstitutionPhoto.objects.update_or_create(
            institution=institution,
            photo_type=photo_type,
            device_type=device_type,
            defaults={'image': image_file}
        )
        serializer = InstitutionPhotoSerializer(photo)
        return Response(serializer.data, status=201 if created else 200)

def api_demo(request):
    return render(request, 'api/demo.html')

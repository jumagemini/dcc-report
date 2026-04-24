from rest_framework import serializers
from reports.models import DCC, Institution, InstitutionPhoto

class DCCSerializer(serializers.ModelSerializer):
    class Meta:
        model = DCC
        fields = ['id', 'name', 'project_name']

class InstitutionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionPhoto
        fields = ['id', 'photo_type', 'device_type', 'image']

class InstitutionSerializer(serializers.ModelSerializer):
    photos = InstitutionPhotoSerializer(many=True, read_only=True)
    dcc_name = serializers.ReadOnlyField(source='dcc.name')
    
    class Meta:
        model = Institution
        fields = '__all__'
        read_only_fields = ['created_at']
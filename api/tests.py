from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from reports.models import DCC, Institution, InstitutionPhoto
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import os

class APIAuthenticationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.auth_header = f'Token {self.token.key}'

    def test_unauthenticated_access(self):
        response = self.client.get('/api/dccs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_access(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)
        response = self.client.get('/api/dccs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_obtain_token_endpoint(self):
        """Test the optional auth token endpoint"""
        url = reverse('api_token_auth')  # now defined
        response = self.client.post(url, {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class DCCAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.dcc = DCC.objects.create(name='Test DCC', project_name='Test Project')

    def test_list_dccs(self):
        response = self.client.get('/api/dccs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test DCC')

    def test_excel_report(self):
        url = reverse('dcc-excel-report', args=[self.dcc.pk])
        # or use explicit path: f'/api/dccs/{self.dcc.pk}/excel_report/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


class InstitutionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.dcc = DCC.objects.create(name='Test DCC', project_name='Test Project')
        # Create institution directly with Object
        self.institution = Institution.objects.create(
            dcc=self.dcc,
            name='Test Institution',
            date_of_installation='2026-04-22',
            contractor_company='ABC Ltd',
            contractor_rep='John Doe',
            icta_rep='',
            indoor_ap1_serial='SN123',
            indoor_ap1_location='Room 1',
            outdoor_ap_serial='OUT456',
            outdoor_ap_location='Outside',
            onu_serial='ONU789',
            onu_location='ICT Room',
            indoor_ap2_serial='',
            indoor_ap2_location='',
            indoor_ap3_serial='',
            indoor_ap3_location='',
            project_no=''
        )
        # Payload for API calls (uses dcc id)
        self.api_payload = {
            'dcc': self.dcc.pk,
            'name': 'Test Institution',
            'date_of_installation': '2026-04-22',
            'contractor_company': 'ABC Ltd',
            'contractor_rep': 'John Doe',
            'icta_rep': '',
            'indoor_ap1_serial': 'SN123',
            'indoor_ap1_location': 'Room 1',
            'outdoor_ap_serial': 'OUT456',
            'outdoor_ap_location': 'Outside',
            'onu_serial': 'ONU789',
            'onu_location': 'ICT Room',
            'indoor_ap2_serial': '',
            'indoor_ap2_location': '',
            'indoor_ap3_serial': '',
            'indoor_ap3_location': '',
            'project_no': ''
        }

    def test_create_institution(self):
        payload = self.api_payload.copy()
        payload['name'] = 'New Institution'
        response = self.client.post('/api/institutions/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Institution.objects.count(), 2)

    def test_list_institutions(self):
        response = self.client.get('/api/institutions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_institution(self):
        url = reverse('institution-detail', args=[self.institution.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Institution')

    def test_update_institution(self):
        url = reverse('institution-detail', args=[self.institution.pk])
        payload = {'name': 'Updated Institution'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.institution.refresh_from_db()
        self.assertEqual(self.institution.name, 'Updated Institution')

    def test_delete_institution(self):
        url = reverse('institution-detail', args=[self.institution.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Institution.objects.count(), 0)

    def test_pdf_endpoint(self):
        url = reverse('institution-pdf', args=[self.institution.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_upload_photo(self):
        url = reverse('institution-upload-photos', args=[self.institution.pk])
        # Dummy image content
        dummy_image_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
            f.write(dummy_image_data)
            f.flush()
            with open(f.name, 'rb') as img:
                response = self.client.post(url, {
                    'photo_type': 'before',
                    'device_type': 'AP1',
                    'image': img
                }, format='multipart')
        os.unlink(f.name)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InstitutionPhoto.objects.count(), 1)

    def test_missing_photo_fields(self):
        url = reverse('institution-upload-photos', args=[self.institution.pk])
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
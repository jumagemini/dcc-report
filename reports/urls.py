from django.urls import path
from . import views

urlpatterns = [
    path('dcc/<int:dcc_id>/add/passive/', views.institution_create, name='institution_create'),
    path('dcc/<int:dcc_id>/add/active/', views.institution_create_active, name='institution_create_active'),
    path('institution/<int:pk>/pdf/', views.generate_institution_pdf, name='institution_pdf'),
    path('institution/<int:pk>/preview/', views.preview_institution_pdf, name='institution_pdf_preview'),
    path('institution/<int:pk>/edit/', views.InstitutionUpdateView.as_view(), name='institution_edit'),
    path('institution/<int:pk>/delete/', views.InstitutionDeleteView.as_view(), name='institution_delete'),
    path('dcc/<int:dcc_id>/institutions/', views.institution_list, name='institution_list'),
    path('dcc/<int:dcc_id>/excel/', views.generate_dcc_excel, name='dcc_excel'),
    path('dcc/<int:dcc_id>/stickers/', views.download_dcc_stickers, name='dcc_stickers'),
    path('institution/<int:pk>/photobucket/', views.download_photo_bucket, name='photo_bucket'),
    path('dcc/<int:dcc_id>/photos/', views.download_dcc_photos, name='dcc_photos'),
    path('institution/<int:pk>/request-delete/', views.request_institution_deletion, name='request_delete'),
    path('notifications/', views.notifications, name='notifications'),
    path('dcc/<int:dcc_id>/photos-word/', views.download_dcc_photos_docx, name='dcc_photos_word'),
    path('dcc/<int:dcc_id>/sheet1/', views.download_sheet1_excel, name='dcc_sheet1'),
    path('api/ocr/', views.ocr_upload, name='ocr_upload'),
    path('api/ocr/status/<str:task_id>/', views.ocr_status, name='ocr_status'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
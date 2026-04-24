from django.urls import path
from . import views

urlpatterns = [
    path('dcc/<int:dcc_id>/add/', views.institution_create, name='institution_create'),
    path('institution/<int:pk>/pdf/', views.generate_institution_pdf, name='institution_pdf'),
    path('institution/<int:pk>/preview/', views.preview_institution_pdf, name='institution_pdf_preview'),
    path('dcc/<int:dcc_id>/excel/', views.generate_dcc_excel, name='dcc_excel'),
]
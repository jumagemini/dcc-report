from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from .models import DCC, Institution, InstitutionPhoto

@admin.register(DCC)
class DCCAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'project_name', 'institution_count', 'excel_download')
    search_fields = ('name', 'project_name')
    actions = ['download_excel_for_selected']

    def institution_count(self, obj):
        return obj.institutions.count()
    institution_count.short_description = 'Number of Institutions'

    def excel_download(self, obj):
        url = reverse('dcc_excel', args=[obj.pk])
        return format_html('<a href="{}" class="button" style="white-space:nowrap;">📥 Download Excel</a>', url)
    excel_download.short_description = 'Excel Report'
    excel_download.allow_tags = True

    def download_excel_for_selected(self, request, queryset):
        if queryset.count() == 1:
            dcc = queryset.first()
            return redirect('dcc_excel', dcc_id=dcc.pk)
        else:
            self.message_user(request, "Please select exactly one DCC to download the Excel report.", level='warning')
    download_excel_for_selected.short_description = "Download Excel for selected DCC"


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'dcc_link', 'date_of_installation', 'contractor_company', 'pdf_preview', 'pdf_download')
    list_filter = ('dcc__name', 'date_of_installation')
    search_fields = ('name', 'contractor_company', 'contractor_rep')
    readonly_fields = ('pdf_preview_link',)

    def dcc_link(self, obj):
        url = reverse('admin:reports_dcc_change', args=[obj.dcc.id])
        return format_html('<a href="{}">{}</a>', url, obj.dcc.name)
    dcc_link.short_description = 'DCC'

    def pdf_preview(self, obj):
        url = reverse('institution_pdf_preview', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">View PDF</a>', url)
    pdf_preview.short_description = 'PDF Preview'

    def pdf_preview_link(self, obj):
        url = reverse('institution_pdf_preview', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Open PDF in new tab</a>', url)
    pdf_preview_link.short_description = 'PDF Preview'

    def pdf_download(self, obj):
        url = reverse('institution_pdf', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Download PDF</a>', url)
    pdf_download.short_description = 'Download PDF'


@admin.register(InstitutionPhoto)
class InstitutionPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'institution', 'photo_type', 'device_type', 'image_preview')
    list_filter = ('photo_type', 'device_type')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'
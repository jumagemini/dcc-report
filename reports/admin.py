import csv
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib import admin
from django.urls import reverse, path
from django.utils import timezone
from django.utils.html import format_html
from django.shortcuts import redirect, render
from django.contrib import messages as django_messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django import forms
from .models import DCC, Institution, InstitutionPhoto, UserProfile, UserDCCLimit, DeletionRequest, Notification

# ====================== User Profile ======================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('allowed_dccs',)

# ====================== DCC ======================
@admin.register(DCC)
class DCCAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'project_name', 'institution_count', 'excel_download', 'stickers')
    search_fields = ('name', 'project_name')
    actions = ['download_excel_for_selected']

    def institution_count(self, obj):
        return obj.institutions.count()
    institution_count.short_description = 'Number of Institutions'

    def excel_download(self, obj):
        url = reverse('dcc_excel', args=[obj.pk])
        return format_html('<a href="{}" class="button" style="white-space:nowrap;">📥 Download Excel</a>', url)
    excel_download.short_description = 'DCC Excel Report'
    excel_download.allow_tags = True

    def download_excel_for_selected(self, request, queryset):
        if queryset.count() == 1:
            dcc = queryset.first()
            return redirect('dcc_excel', dcc_id=dcc.pk)
        else:
            self.message_user(request, "Please select exactly one DCC to download the Excel report.", level='warning')
    download_excel_for_selected.short_description = "Download Excel for selected DCC"

    def stickers(self, obj):
        url = reverse('dcc_stickers', args=[obj.pk])
        return format_html('<a href="{}" class="button" style="white-space:nowrap;">📥 Download Labels</a>', url)
    stickers.short_description = 'DCC Device Labels (DOCX)'

# ====================== UserDCCLimit ======================
@admin.register(UserDCCLimit)
class UserDCCLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'dcc', 'max_institutions')
    list_filter = ('dcc',)
    search_fields = ('user__username',)

# ====================== Institution Messaging ======================
class SendMessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, label='Message to user')

def send_message_to_creator(modeladmin, request, queryset):
    ids = ','.join(str(obj.pk) for obj in queryset)
    url = reverse('admin:send_message_view') + f'?ids={ids}'
    return HttpResponseRedirect(url)
send_message_to_creator.short_description = "Send notification to creator(s)"

def send_message_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Admin only")
    ids = request.GET.get('ids', '')
    institution_ids = [int(i) for i in ids.split(',') if i.strip()]
    institutions = Institution.objects.filter(pk__in=institution_ids)

    if request.method == 'POST':
        form = SendMessageForm(request.POST)
        if form.is_valid():
            message_text = form.cleaned_data['message']
            for inst in institutions:
                if inst.created_by:
                    Notification.objects.create(
                        user=inst.created_by,
                        sender=request.user,
                        institution=inst,
                        message=message_text
                    )
            django_messages.success(request, f"Sent message to {len(institutions)} institution creator(s).")
            return HttpResponseRedirect(reverse('admin:reports_institution_changelist'))
    else:
        form = SendMessageForm()

    return render(request, 'admin/send_message.html', {
        'form': form,
        'institutions': institutions,
        'ids': ids,
    })

# ====================== Institution ======================
@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'dcc_link', 'date_of_installation', 'contractor_company', 'pdf_preview', 'pdf_download')
    list_filter = ('dcc__name', 'date_of_installation')
    search_fields = ('name', 'contractor_company', 'contractor_rep')
    readonly_fields = ('pdf_preview_link',)
    actions = [send_message_to_creator]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-message/', self.admin_site.admin_view(send_message_view), name='send_message_view'),
        ]
        return custom_urls + urls

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

# ====================== InstitutionPhoto ======================
@admin.register(InstitutionPhoto)
class InstitutionPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'institution', 'photo_type', 'device_type', 'image_preview')
    list_filter = ('photo_type', 'device_type')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Preview'

# ====================== Deletion Request Actions ======================
def approve_deletion_requests(modeladmin, request, queryset):
    for req in queryset.filter(status='pending'):
        req.status = 'approved'
        req.approved_by = request.user
        req.save()
        req.institution.delete()
        Notification.objects.create(
            user=req.requested_by,
            institution=req.institution,
            message=f"Deletion of '{req.institution.name}' has been approved."
        )
approve_deletion_requests.short_description = "Approve selected deletion requests"

def reject_deletion_requests(modeladmin, request, queryset):
    for req in queryset.filter(status='pending'):
        req.status = 'rejected'
        req.approved_by = request.user
        req.save()
        reason_text = f" Reason: {req.reason}" if req.reason else ""
        Notification.objects.create(
            user=req.requested_by,
            institution=req.institution,
            message=f"Deletion of '{req.institution.name}' was rejected.{reason_text}"
        )
reject_deletion_requests.short_description = "Reject selected deletion requests"

class RejectReasonForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Reason for rejection',
        required=True
    )

def reject_with_reason(modeladmin, request, queryset):
    ids = ','.join(str(obj.pk) for obj in queryset)
    url = reverse('admin:reject_deletion_requests_view') + f'?ids={ids}'
    return HttpResponseRedirect(url)
reject_with_reason.short_description = "Reject selected requests (with reason)"

def reject_deletion_requests_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Admin only")
    ids = request.GET.get('ids', '')
    request_ids = [int(i) for i in ids.split(',') if i.strip()]
    requests_list = DeletionRequest.objects.filter(pk__in=request_ids, status='pending')

    if request.method == 'POST':
        form = RejectReasonForm(request.POST)
        if form.is_valid():
            reason_text = form.cleaned_data['reason']
            for req in requests_list:
                req.status = 'rejected'
                req.reason = reason_text
                req.approved_by = request.user
                req.save()
                Notification.objects.create(
                    user=req.requested_by,
                    institution=req.institution,
                    message=f"Deletion of '{req.institution.name}' was rejected. Reason: {reason_text}"
                )
            django_messages.success(request, f"Rejected {len(requests_list)} deletion request(s).")
            return HttpResponseRedirect(reverse('admin:reports_deletionrequest_changelist'))
    else:
        form = RejectReasonForm()

    return render(request, 'admin/reject_deletion_requests.html', {
        'form': form,
        'requests': requests_list,
        'ids': ids,
    })

# ====================== DeletionRequest (one registration) ======================
@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('institution', 'requested_by', 'status', 'created_at')
    list_filter = ('status',)
    actions = [approve_deletion_requests, reject_deletion_requests, reject_with_reason]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('reject-reason/', self.admin_site.admin_view(reject_deletion_requests_view), name='reject_deletion_requests_view'),
        ]
        return custom_urls + urls

# ====================== Notification ======================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'sender', 'institution', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message', 'institution__name')
    autocomplete_fields = ['user', 'sender', 'institution']
    date_hierarchy = 'created_at'
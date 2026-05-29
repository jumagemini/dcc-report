from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class DCC(models.Model):
    name = models.CharField(max_length=100, unique=True)
    project_name = models.CharField(max_length=100, default="DHS")

    def __str__(self):
        return self.name
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    allowed_dccs = models.ManyToManyField('DCC', blank=True)
    signature = models.ImageField(upload_to='user_signatures/', blank=True, null=True)

    def __str__(self):
        return self.user.username    
    
class UserDCCLimit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dcc = models.ForeignKey(DCC, on_delete=models.CASCADE)
    max_institutions = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Leave empty for unlimited."
    )

    class Meta:
        unique_together = ('user', 'dcc')

    def __str__(self):
        return f"{self.user.username} – {self.dcc.name} (max: {self.max_institutions or '∞'})"    

class Institution(models.Model):
    project_no = models.CharField(max_length=50, blank=True, verbose_name="Project No.", default='')
    dcc = models.ForeignKey(DCC, on_delete=models.CASCADE, related_name='institutions')
    name = models.CharField(max_length=200)
    date_of_installation = models.DateField()
    contractor_company = models.CharField(max_length=200)
    contractor_rep = models.CharField(max_length=100)
    icta_rep = models.CharField(max_length=100, blank=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)

    # Indoor AP1 (mandatory)
    indoor_ap1_serial = models.CharField(max_length=50)
    indoor_ap1_location = models.CharField(max_length=100)

    # Indoor AP2 (optional)
    indoor_ap2_serial = models.CharField(max_length=50, blank=True)
    indoor_ap2_location = models.CharField(max_length=100, blank=True)

    # Indoor AP3 (optional)
    indoor_ap3_serial = models.CharField(max_length=50, blank=True)
    indoor_ap3_location = models.CharField(max_length=100, blank=True)

    # Outdoor AP
    outdoor_ap_serial = models.CharField(max_length=50)
    outdoor_ap_location = models.CharField(max_length=100)

    # ONU / OHU
    onu_serial = models.CharField(max_length=50)
    onu_location = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='institutions_created'
    )

    def __str__(self):
        return f"{self.name} ({self.dcc.name})"

class InstitutionPhoto(models.Model):
    PHOTO_TYPES = (
        ('before', 'Before Installation'),
        ('after', 'After Installation'),
    )
    DEVICE_TYPES = (
        ('ONU', 'ONU'),
        ('AP1', 'Indoor AP1'),
        ('AP2', 'Indoor AP2'),
        ('AP3', 'Indoor AP3'),
        ('OUT', 'Outdoor AP1'),
    )
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='photos')
    photo_type = models.CharField(max_length=10, choices=PHOTO_TYPES)
    device_type = models.CharField(max_length=3, choices=DEVICE_TYPES, default='ONU')
    image = models.ImageField(upload_to='installation_photos/')

    class Meta:
        unique_together = ('institution', 'photo_type', 'device_type')  # one photo per device per type

    def __str__(self):
        return f"{self.institution.name} - {self.photo_type}"

class DeletionRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='deletion_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True, null=True, help_text="Admin may give a reason for rejection/approval")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='approved_deletions')

    def __str__(self):
        return f"Deletion of {self.institution.name} by {self.requested_by.username} [{self.status}]"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    institution = models.ForeignKey('Institution', on_delete=models.SET_NULL, null=True, blank=True)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)   # optional URL
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.message[:50]}"

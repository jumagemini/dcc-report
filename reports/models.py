from django.db import models

class DCC(models.Model):
    name = models.CharField(max_length=100, unique=True)
    project_name = models.CharField(max_length=100, default="DHS")

    def __str__(self):
        return self.name

class Institution(models.Model):
    project_no = models.CharField(max_length=50, blank=True, verbose_name="Project No.", default='')
    dcc = models.ForeignKey(DCC, on_delete=models.CASCADE, related_name='institutions')
    name = models.CharField(max_length=200)
    date_of_installation = models.DateField()
    contractor_company = models.CharField(max_length=200)
    contractor_rep = models.CharField(max_length=100)
    icta_rep = models.CharField(max_length=100, blank=True)

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

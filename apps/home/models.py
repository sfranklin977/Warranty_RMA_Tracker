from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = [('NEW','New'),('FILED','Filed'),('PAID','Paid')]

class WarrantyClaim(models.Model):
    servicetitan_job_id = models.CharField(max_length=100, blank=True, null=True)
    servicetitan_form_id = models.CharField(max_length=100, blank=True, null=True)
    servicetitan_submission_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    servicetitan_synced_at = models.DateTimeField(blank=True, null=True)
    # ServiceTitan auto-populated fields (from Warranty Return Form)
    job_number = models.CharField(max_length=50, blank=True, null=True)
    tech_name = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    client_address = models.CharField(max_length=300, blank=True, null=True)
    equipment_brand = models.CharField(max_length=100, blank=True, null=True)
    unit_model = models.CharField(max_length=100, blank=True, null=True)
    unit_serial = models.CharField(max_length=100, blank=True, null=True)
    warranty_type = models.CharField(max_length=100, blank=True, null=True)
    part_type = models.CharField(max_length=200, blank=True, null=True)
    equipment_location = models.CharField(max_length=200, blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    compressor_image = models.URLField(max_length=500, blank=True, null=True)
    claim_date = models.DateField(blank=True, null=True)

    # Financial / tracking
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')

    # Vendor / submission
    vendor = models.CharField(max_length=100, blank=True, null=True)
    vendor_submission_method = models.CharField(max_length=100, blank=True, null=True)
    vendor_confirmation_number = models.CharField(max_length=100, blank=True, null=True)
    vendor_submitted_date = models.DateField(blank=True, null=True)

    # Notes
    notes = models.TextField(blank=True, null=True)

    # Owner
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Claim #{self.id} - {self.customer_name or 'N/A'} ({self.get_status_display()})"

from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = [('NEW','New'),('FILED','Filed'),('PAID','Paid')]

class PartsReturn(models.Model):
    # Spreadsheet-matching fields
    client_name = models.CharField(max_length=200, blank=True, null=True)
    order_no = models.CharField(max_length=100, blank=True, null=True)
    part_amt = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    part_name = models.CharField(max_length=200, blank=True, null=True)
    model_no = models.CharField(max_length=100, blank=True, null=True)
    serial_no = models.CharField(max_length=100, blank=True, null=True)
    rma_no = models.CharField(max_length=100, blank=True, null=True)
    date_rma_requested = models.DateField(blank=True, null=True)
    date_part_returned = models.DateField(blank=True, null=True)
    credit_received = models.DateField(blank=True, null=True)
    rma_credit_received = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    replacement_ordered_date = models.DateField(blank=True, null=True)

    # Legacy fields (keep for existing data)
    part_number = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    job_number = models.CharField(max_length=50, blank=True, null=True)
    tech_name = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    return_date = models.DateField(blank=True, null=True)
    vendor = models.CharField(max_length=100, blank=True, null=True)
    rma_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')
    notes = models.TextField(blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parts_returns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"RMA #{self.id} - {self.client_name or self.part_name or 'N/A'}"

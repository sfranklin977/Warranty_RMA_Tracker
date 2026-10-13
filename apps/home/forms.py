from django import forms
from .models import WarrantyClaim

class WarrantyClaimForm(forms.ModelForm):
    class Meta:
        model = WarrantyClaim
        fields = [
            'job_number', 'tech_name', 'customer_name', 'client_address',
            'equipment_brand', 'unit_model', 'unit_serial', 'warranty_type',
            'part_type', 'equipment_location', 'diagnosis', 'compressor_image',
            'claim_date', 'claim_amount', 'status',
            'vendor', 'vendor_submission_method', 'vendor_confirmation_number',
            'vendor_submitted_date', 'notes',
        ]
        widgets = {
            'job_number': forms.TextInput(attrs={'class':'form-input'}),
            'tech_name': forms.TextInput(attrs={'class':'form-input'}),
            'customer_name': forms.TextInput(attrs={'class':'form-input'}),
            'client_address': forms.TextInput(attrs={'class':'form-input'}),
            'equipment_brand': forms.TextInput(attrs={'class':'form-input'}),
            'unit_model': forms.TextInput(attrs={'class':'form-input'}),
            'unit_serial': forms.TextInput(attrs={'class':'form-input'}),
            'warranty_type': forms.TextInput(attrs={'class':'form-input'}),
            'part_type': forms.TextInput(attrs={'class':'form-input'}),
            'equipment_location': forms.TextInput(attrs={'class':'form-input'}),
            'diagnosis': forms.Textarea(attrs={'class':'form-input','rows':3}),
            'compressor_image': forms.URLInput(attrs={'class':'form-input'}),
            'claim_date': forms.DateInput(attrs={'class':'form-input','type':'date'}),
            'claim_amount': forms.NumberInput(attrs={'class':'form-input','step':'0.01'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'vendor': forms.TextInput(attrs={'class':'form-input'}),
            'vendor_submission_method': forms.TextInput(attrs={'class':'form-input'}),
            'vendor_confirmation_number': forms.TextInput(attrs={'class':'form-input'}),
            'vendor_submitted_date': forms.DateInput(attrs={'class':'form-input','type':'date'}),
            'notes': forms.Textarea(attrs={'class':'form-input','rows':3}),
        }

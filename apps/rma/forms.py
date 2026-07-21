from django import forms
from . import models as rma_models


class PartsReturnForm(forms.ModelForm):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), required=False
    )
    date_rma_requested = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), required=False
    )
    date_rma_credit_received = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), required=False
    )
    replacement_ordered_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), required=False
    )

    class Meta:
        model = rma_models.PartsReturn
        fields = [
            'client_name', 'order_number', 'invoice_amount',
            'model_number', 'serial_number',
            'rma_number', 'date_rma_requested', 'date_rma_credit_received',
            'rma_credit_received',
            'replacement_ordered_date', 'replacement_order_number',
            'notes',
        ]

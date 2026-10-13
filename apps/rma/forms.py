from django import forms
from .models import PartsReturn

class PartsReturnForm(forms.ModelForm):
    class Meta:
        model = PartsReturn
        fields = [
            'client_name', 'order_no', 'part_amt', 'part_name', 'model_no',
            'serial_no', 'rma_no', 'date_rma_requested', 'date_part_returned',
            'credit_received', 'rma_credit_received', 'replacement_ordered_date',
            'status', 'notes',
        ]
        widgets = {
            'client_name': forms.TextInput(attrs={'class':'form-input'}),
            'order_no': forms.TextInput(attrs={'class':'form-input'}),
            'part_amt': forms.NumberInput(attrs={'class':'form-input','step':'0.01'}),
            'part_name': forms.TextInput(attrs={'class':'form-input'}),
            'model_no': forms.TextInput(attrs={'class':'form-input'}),
            'serial_no': forms.TextInput(attrs={'class':'form-input'}),
            'rma_no': forms.TextInput(attrs={'class':'form-input'}),
            'date_rma_requested': forms.DateInput(attrs={'class':'form-input','type':'date'}),
            'date_part_returned': forms.DateInput(attrs={'class':'form-input','type':'date'}),
            'credit_received': forms.DateInput(attrs={'class':'form-input','type':'date'}),
            'rma_credit_received': forms.NumberInput(attrs={'class':'form-input','step':'0.01'}),
            'replacement_ordered_date': forms.DateInput(attrs={'class':'form-input','type':'date'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'notes': forms.Textarea(attrs={'class':'form-input','rows':3}),
        }

class PartsReturnImportForm(forms.Form):
    csv_file = forms.FileField(
        label='Select CSV file',
        widget=forms.FileInput(attrs={'class':'form-input','accept':'.csv'})
    )

from django import forms
from django.core.exceptions import ValidationError
from .models import Institution

class MultipleFileInput(forms.ClearableFileInput):
    """Widget that allows multiple file selection."""
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True
        super().__init__(attrs)

class MultipleFileField(forms.FileField):
    """Field that returns a list of uploaded files."""
    widget = MultipleFileInput

    def to_python(self, data):
        if data is None:
            return []
        # data may be a single file or list of files from request.FILES
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super(MultipleFileField, self).to_python(f) for f in data]

    def validate(self, value):
        if value:
            for f in value:
                super().validate(f)

class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        exclude = ['dcc']  # exclude dcc, we'll set it manually
        widgets = {
            'date_of_installation': forms.DateInput(attrs={'type': 'date'}),
        }
        def clean_icta_rep(self):
            data = self.cleaned_data.get('icta_rep')
            if data and data.strip().upper() == 'NA':
                return ''
            return data

class PhotoUploadForm(forms.Form):
    
    # Before photos for each device
    before_onu = forms.ImageField(required=False, label='Before - ONU')
    before_ap1 = forms.ImageField(required=False, label='Before - Indoor AP1')
    before_ap2 = forms.ImageField(required=False, label='Before - Indoor AP2')
    before_ap3 = forms.ImageField(required=False, label='Before - Indoor AP3')
    before_out = forms.ImageField(required=False, label='Before - Outdoor AP1')

    # After photos for each device
    after_onu = forms.ImageField(required=False, label='After - ONU')
    after_ap1 = forms.ImageField(required=False, label='After - Indoor AP1')
    after_ap2 = forms.ImageField(required=False, label='After - Indoor AP2')
    after_ap3 = forms.ImageField(required=False, label='After - Indoor AP3')
    after_out = forms.ImageField(required=False, label='After - Outdoor AP1')
from django import forms
from .models import PDFFile

class PDFFileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PDFFileForm, self).__init__(*args, **kwargs)
        self.fields['classroom'].queryset = self.fields['classroom'].queryset.order_by('name')
        if 'classroom' in self.initial:
            self.fields['subject'].queryset = Subject.objects.filter(classroom=self.initial['classroom']).order_by('name')
        else:
            self.fields['subject'].queryset = Subject.objects.none()
        
    class Meta:
        model = PDFFile
        fields = ['title','category','classroom','subject','file']
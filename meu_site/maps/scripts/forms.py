from django import forms

class UploadCSVForm(forms.Form):
    arquivo = forms.FileField(label='Choose a CSV file')

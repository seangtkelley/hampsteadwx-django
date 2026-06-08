"""Django forms for monthly summary submission and remark editing."""

from django import forms


class SubmitMonthlyCSV(forms.Form):
    """Form for uploading a monthly observation CSV file."""

    csv_file = forms.FileField()
    password = forms.CharField(max_length=64)


class EditRemarks(forms.Form):
    """Form for editing monthly summary remarks."""

    remarks = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(max_length=64)

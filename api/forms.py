from django import forms


class SubmitMonthlyCSV(forms.Form):
    csv_file = forms.FileField()
    password = forms.CharField(max_length=64)


class EditRemarks(forms.Form):
    remarks = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(max_length=64)
from django import forms


class SubmitMonthlyCSV(forms.Form):
    password = forms.CharField(max_length=64)
    csv_file = forms.FileField()
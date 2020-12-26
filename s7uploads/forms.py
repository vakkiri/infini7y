from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Review, Upload

class SignUpForm(UserCreationForm):
    email = forms.EmailField(help_text = '*')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('title', 'text', 'rating')


class SearchForm(forms.Form):
    search_line = forms.CharField(max_length=200)

    def __init__(self):
        super(SearchForm, self).__init__()
        self.fields['search_line'].widget.attrs.update({
            'placeholder': '  Search infini7y...',
            'onfocus': "this.placeholder=''"
            })


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    description = forms.CharField()
    versionNotes = forms.CharField(required=False)
    versionNumber = forms.CharField(max_length=5)
    file = forms.FileField()
    screenshots = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)
    tagline = forms.CharField(required=False)


class EditUploadForm(forms.Form):
    title = forms.CharField(max_length=50)
    description = forms.CharField()
    versionNotes = forms.CharField(required=False)
    versionNumber = forms.CharField(max_length=5)
    tagline = forms.CharField(required=False)


class NewVersionForm(forms.Form):
    description = forms.CharField()
    versionNotes = forms.CharField(required=True)
    versionNumber = forms.CharField(max_length=5, required=True)
    tagline = forms.CharField(required=False)



class AddScreenshotForm(forms.Form):
    screenshots = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))



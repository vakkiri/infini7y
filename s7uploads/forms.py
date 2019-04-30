from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Review

class SignUpForm(UserCreationForm):
	email = forms.EmailField(help_text = '*')

	class Meta:
		model = User
		fields = ('username', 'email', 'password1', 'password2', )

class ReviewForm(forms.ModelForm):
	class Meta:
		model = Review
		fields = ('title', 'text', 'rating')

class UploadFileForm(forms.Form):
        title = forms.CharField(max_length=50)
        description = forms.CharField()
        versionNotes = forms.CharField(required=False)
        versionNumber = forms.DecimalField(max_digits=5, decimal_places=1)
        file = forms.FileField()
        screenshots = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}), required=False)



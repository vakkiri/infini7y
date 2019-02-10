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

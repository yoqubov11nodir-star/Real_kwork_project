from django import forms
from django.contrib.auth.models import User
from .models import Profile, Vacancy  

class RegisterForm(forms.Form):
    ROLE_CHOICES = [
        ('freelancer', 'Frilanser'),
        ('client', 'Mijoz'),
    ]
    first_name = forms.CharField(
        max_length=50, label="Ism",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Isming'})
    )
    last_name = forms.CharField(
        max_length=50, label="Familiya",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiyaning'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@gmail.com'})
    )
    password1 = forms.CharField(
        label="Parol", min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    password2 = forms.CharField(
        label="Parolni takrorlang",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.HiddenInput(), initial='freelancer')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu email allaqachon ro'yxatdan o'tgan")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Parollar bir xil emas")
        return cleaned

    def save(self):
        data = self.cleaned_data
        base = f"{data['first_name'].lower()}{data['last_name'].lower()}"
        base = ''.join(c for c in base if c.isalnum())[:20] or 'user'
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1
        user = User.objects.create_user(
            username=username,
            email=data['email'],
            password=data['password1'],
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        user.profile.role = data.get('role', 'freelancer')
        user.profile.save()
        return user

class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = [
            'title', 'description', 'category',
            'budget_min', 'budget_max',
            'deadline_days', 'required_workers',
            'required_skills', 'is_team_project'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vakansiya nomi...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 6,
                'placeholder': 'Batafsil tavsif...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'budget_min': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '100'
            }),
            'budget_max': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '500'
            }),
            'deadline_days': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '7'
            }),
            'required_workers': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '1'
            }),
            'required_skills': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Python, Django, React...'
            }),
            'is_team_project': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Vakansiya nomi',
            'description': 'Tavsif',
            'category': 'Kategoriya',
            'budget_min': 'Minimal narx ($)',
            'budget_max': 'Maksimal narx ($)',
            'deadline_days': 'Muddat (kun)',
            'required_workers': 'Nechta worker kerak',
            'required_skills': "Kerakli ko'nikmalar",
            'is_team_project': 'Jamoa loyihasi (PM tayinlanadi)',
        }

class ProfileForm(forms.ModelForm):
    # Bu yerda widget qo'shildi dizayn buzilmasligi uchun
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Profile
        fields = ['bio', 'skills', 'avatar', 'hourly_rate', 'portfolio_url', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django...'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Toshkent, O\'zbekiston'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            
            # AGAR FOYDALANUVCHI KOMPANIYA BO'LSA:
            if self.instance.role == 'client':
                self.fields['first_name'].label = "Kompaniya nomi"
                self.fields['last_name'].label = "Kompaniya turi (MChJ, XK va hk)"
                self.fields['bio'].label = "Kompaniya haqida ma'lumot"
                self.fields['portfolio_url'].label = "Kompaniya veb-sayti"
                # Kompaniyaga kerak bo'lmagan maydonlarni yashiramiz
                self.fields['hourly_rate'].widget = forms.HiddenInput()
                self.fields['skills'].widget = forms.HiddenInput()
            else:
                # Frilanser uchun odatiy holat
                self.fields['first_name'].label = "Ism"
                self.fields['last_name'].label = "Familiya"
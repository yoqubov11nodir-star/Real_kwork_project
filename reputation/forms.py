from django import forms
from .models import Review

SCORE_CHOICES = [(i, '⭐' * i) for i in range(1, 6)]


class ReviewForm(forms.ModelForm):
    communication_score = forms.ChoiceField(
        choices=SCORE_CHOICES, label='Muloqot sifati',
        widget=forms.RadioSelect(attrs={'class': 'star-radio'})
    )
    quality_score = forms.ChoiceField(
        choices=SCORE_CHOICES, label='Ish sifati',
        widget=forms.RadioSelect(attrs={'class': 'star-radio'})
    )
    deadline_score = forms.ChoiceField(
        choices=SCORE_CHOICES, label='Vaqtida topshirish',
        widget=forms.RadioSelect(attrs={'class': 'star-radio'})
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Frilanser bilan ishlash tajribangizni ulashing...'
        }),
        label='Sharh'
    )

    class Meta:
        model = Review
        fields = ['communication_score', 'quality_score', 'deadline_score', 'comment']

    def clean_communication_score(self):
        return int(self.cleaned_data['communication_score'])

    def clean_quality_score(self):
        return int(self.cleaned_data['quality_score'])

    def clean_deadline_score(self):
        return int(self.cleaned_data['deadline_score'])

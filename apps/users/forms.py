# apps/users/forms.py
from django import forms
from .models import UserPreference

class PreferenceForm(forms.ModelForm):
    domains = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'e.g., health, tech, sports'}),
        help_text="Comma-separated interest domains"
    )
    mental_state = forms.ChoiceField(
        choices=[('', '---'), ('stressed', 'Stressed'), ('happy', 'Happy'), ('neutral', 'Neutral')],
        required=False
    )
    min_sentiment = forms.FloatField(
        min_value=0.0, max_value=1.0, required=False,
        help_text="Minimum sentiment (0.0 = any, 1.0 = only very positive)"
    )

    class Meta:
        model = UserPreference
        fields = ['domains', 'mental_state', 'min_sentiment', 'preferences_text']
        widgets = {'preferences_text': forms.Textarea(attrs={'rows': 3})}

    def clean_domains(self):
        data = self.cleaned_data['domains']
        return [d.strip().lower() for d in data.split(',') if d.strip()]
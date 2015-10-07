from django import forms
from notecards.models import Deck, Card


class deckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ['title', 'description']


class cardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['front', 'back']

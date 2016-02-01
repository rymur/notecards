from django import forms

from notecards.models import Card, Deck


class cardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['front', 'back']


class deckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ['title', 'description', 'tags']

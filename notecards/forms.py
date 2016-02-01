from django import forms

from notecards.models import Card, Deck


class cardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['front', 'back']

    def __init__(self, *args, **kwargs):
        super(cardForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs['class'] = 'fullwidth'


class deckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ['title', 'description', 'tags']

    def __init__(self, *args, **kwargs):
        super(deckForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs['class'] = 'fullwidth'

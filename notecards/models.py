from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django.core import urlresolvers

from taggit.managers import TaggableManager


class Deck(models.Model):
    author = models.ForeignKey(User)
    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=256)
    description = models.TextField(blank=True)
    tags = TaggableManager(blank=True)
    dateCreated = models.DateField(auto_now_add=True)
    dateModified = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=True)

    class Meta:
        unique_together = ('author', 'title')

    def save(self, *args, **kwargs):
        if Deck.objects.filter(author=self.author).count() >= 100:
            raise ValidationError('User cannot have more than 100 decks')
        self.slug = slugify(self.title)
        super(Deck, self).save(*args, **kwargs)

    @property
    def numCards(self):
        return self.card_set.count()

    def get_absolute_url(self):
        return "{0}?did={1}".format(urlresolvers.reverse('view_deck'),
                                    self.id)

    def __repr__(self):
        return self.title


class Card(models.Model):
    front = models.CharField(max_length=512)
    back = models.CharField(max_length=512)
    deck = models.ForeignKey(Deck)
    score = models.IntegerField(default=0)

    def __repr__(self):
        return self.front + ' - ' + self.back

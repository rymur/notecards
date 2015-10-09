from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from taggit.managers import TaggableManager


class Deck(models.Model):
    author = models.ForeignKey(User)
    title = models.CharField(max_length=256, blank=True)
    slug = models.SlugField(max_length=256)
    description = models.TextField(blank=True)
    tags = TaggableManager(blank=True)
    dateCreated = models.DateField(auto_now_add=True)
    dateModified = models.DateTimeField(auto_now=True)
    # This one may not be needed. Further research required.
    # parent = models.ForeignKey('self', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Deck, self).save(*args, **kwargs)

    @property
    def numCards(self):
        return self.card_set.count()

    def __repr__(self):
        return self.title


class Card(models.Model):
    front = models.CharField(max_length=512)
    back = models.CharField(max_length=512)
    deck = models.ForeignKey(Deck)
    score = models.IntegerField(default=0)

    def __repr__(self):
        return self.front + ' - ' + self.back

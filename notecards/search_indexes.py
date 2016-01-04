import datetime
from haystack import indexes
from notecards.models import Deck


class CardIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    tags = indexes.MultiValueField()

    def prepare_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    def get_model(self):
        return Deck

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            dateCreated__lte=datetime.datetime.now()).filter(
            published=True)

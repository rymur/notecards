from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from notecards import views

urlpatterns = [
                 url(r'^$',
                     views.index,
                     name='index'),
                 url(r'^get_card/(?P<deckid>[0-9]+)/$',
                     views.get_card,
                     name='get_card'),
                 url(r'^gwc/(?P<deckid>[0-9]+)/$',
                     views.get_weak_card,
                     name='get_weak_card'),
                 url(r'^get_deck/(?P<deckid>[0-9]+)/$',
                     views.get_deck,
                     name='get_deck'),
                 url(r'^check_answer/(?P<deckid>[0-9]+)/$',
                     views.check_answer,
                     name='check_answer'),
                 url(r'^create_deck/$',
                     views.create_deck,
                     name='create_deck'),
                 url(r'^create_card/(?P<deckid>[0-9]+)/$',
                     views.create_card,
                     name='create_card'),
                 url(r'^edit_card/(?P<cardid>[0-9]+)/$',
                     views.edit_card,
                     name='edit_card'),
                 url(r'^edit_deck/(?P<deckid>[0-9]+)/$',
                     views.edit_deck,
                     name='edit_deck'),
                 url(r'^deck/$',
                     views.view_deck,
                     name='view_deck'),
                 url(r'^decks/$',
                     views.get_decks,
                     name='decks'),
                 url(r'^decks/(?P<user>[\w\-]+)/$',
                     views.get_user_decks,
                     name='get_user_decks'),
                 url(r'^clone_deck/$',
                     views.clone_deck,
                     name='clone_deck'),
                 url(r'^delete/$',
                     views.delete_deck,
                     name='delete_deck'),
                 url(r'^publish/$',
                     views.publish_deck,
                     name='publish'),
                 ]

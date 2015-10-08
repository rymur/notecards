from django.conf.urls import patterns, url
from notecards import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^get_card/(?P<title_slug>[\w\-]+)/$', views.get_card, name='get_card'),
                       url(r'^get_deck/(?P<title_slug>[\w\-]+)/$', views.get_deck, name='get_deck'),
                       url(r'^check_answer/(?P<title_slug>[\w\-]+)/$', views.check_answer, name='check_answer'),
                       url(r'^create_deck/$', views.create_deck, name='create_deck'),
                       url(r'^create_card/(?P<deck_slug>[\w\-]+)/$', views.create_card, name='create_card'),
                       url(r'^get_all_decks/$', views.get_all_decks, name='get_all_decks'),
                       url(r'^get_user_decks/(?P<user>[\w\-]+)/$', views.get_user_decks, name='get_user_decks'),
                       url(r'^clone_deck/$', views.clone_deck, name='clone_deck'),
                       url(r'^login/$', views.user_login, name='login'),
                       url(r'^logout/$', views.user_logout, name='logout'),
                       url(r'^register/$', views.register, name='register'),
                       )

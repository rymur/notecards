from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core import serializers
from django.core.urlresolvers import reverse
from django.db.models import Max, Min, F
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from notecards.models import Deck, Card
from notecards.forms import deckForm, cardForm

import random


def index(request):
    return render(request, 'notecards/index.html', {})


def register(request):
    if (request.method == "POST") and (not request.user.is_authenticated()):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('index'))
    elif request.method == "GET" and (not request.user.is_authenticated()):
        form = UserCreationForm()
        return render(request, 'notecards/register.html', {'form': form})
    else:
        return HttpResponse("You are already registered!")


@login_required
def check_answer(request, title_slug):
    userID = request.user.id
    user = User.objects.get(pk=userID)
    deck = get_object_or_404(Deck, author=user, slug=title_slug)
    front = request.POST.get('front')
    userAnswer = request.POST.get('ans')
    answerCards = Card.objects.filter(deck=deck, front=front)
    for ans in answerCards:
        if ans.back == userAnswer:
            ans.score += 1
            ans.save()
            return HttpResponse('correct')
    answerCards.update(score=F('score') - 1)
    return HttpResponse('wrong')


@login_required
def get_card(request, title_slug):
    userID = request.user.id
    user = User.objects.get(pk=userID)
    deck = Deck.objects.filter(author=user, slug=title_slug)
    minScore = deck.aggregate(Min('card__score'))
    minScore = minScore['card__score__min']
    maxScore = deck.aggregate(Max('card__score'))
    maxScore = maxScore['card__score__max']
    rscore = random.randint(minScore, maxScore)
    deck = deck[0]
    cards = deck.card_set.filter(score__lte=rscore)
    rindex = random.randint(0, len(cards) - 1)
    card = cards[rindex]

    card_json = serializers.serialize('json', [card])
    return HttpResponse(card_json, content_type='application/json')


def get_deck(request, title_slug):
    deck = get_object_or_404(Deck, slug=title_slug)
    cards = deck.card_set.all()
    cardsJSON = serializers.serialize('json', cards)

    return HttpResponse(cardsJSON, content_type='application/json')


def get_all_decks(request):
    decks = Deck.objects.all()
    decksJSON = serializers.serialize('json', decks)

    return HttpResponse(decksJSON, content_type='application/json')


def get_decks(request):
    if request.method == 'GET':
        decks = Deck.objects.order_by('-dateCreated')[:50]
        return render(request, 'notecards/decks.html', {'decks': decks})
    elif request.method == 'POST':
        page = int(request.POST.get('page_num'))
        start = page * 50
        end = start + 50
        decks = Deck.objects.order_by('-dateCreated')[start:end]
        decksJSON = serializers.serialize('json', decks)
        return HttpResponse(decksJSON, content_type='application/json')


def get_user_decks(request, user):
    user = User.objects.get(username=user)
    decks = Deck.objects.filter(author=user)
    decksJSON = serializers.serialize('json', decks)

    return HttpResponse(decksJSON, content_type='application/json')


@login_required
def create_deck(request):
    if request.method == 'POST':
        form = deckForm(request.POST)
        if form.is_valid():
            userID = request.user.id
            user = User.objects.get(pk=userID)
            title = form.cleaned_data['title']
            desc = form.cleaned_data['description']
            deck = Deck(author=user, title=title, description=desc)
            deck.save()
            for tag in form.cleaned_data['tags']:
                deck.tags.add(tag)
            deck.save()
            return HttpResponseRedirect(reverse('decks'))
            # TODO: handle case where form isn't valid
    form = deckForm()
    # TODO: render new form
    return render(request, 'notecards/create_deck.html', {'form': form})


@login_required
def create_card(request, deck_slug):
    if request.method == 'POST':
        userID = request.user.id
        user = User.objects.get(pk=userID)
        deck = Deck.objects.get(slug=deck_slug, author=user)
        form = cardForm(request.POST)
        if form.is_valid():
            front = form.cleaned_data['front']
            back = form.cleaned_data['back']
            card = Card(front=front, back=back, deck=deck)
            card.save()
            return HttpResponse('success')
        else:
            return HttpResponse('Error: You do not own this deck')

    form = cardForm()


@login_required
def clone_deck(request):
    deckName = request.POST.get('deck')
    userID = request.user.id
    user = User.objects.get(pk=userID)
    deck = Deck.objects.get(title=deckName)
    if deck.author != user:
        newDeck = Deck(author=user,
                       title=deck.title,
                       slug=deck.slug,
                       description=deck.description,
                       )
        newDeck.save()
        tags = deck.tags.names()
        for tag in tags:
            newDeck.tags.add(tag)
        newDeck.save()
        for card in deck.card_set.all():
            newCard = Card(front=card.front,
                           back=card.back,
                           deck=newDeck,
                           score=0)
            newCard.save()
        # return HTTP 201 - "created"
        return HttpResponse(status=201)
    else:
        return HttpResponse('Error: You already own this deck')

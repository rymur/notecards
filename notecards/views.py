from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect  
from django.core import serializers
from django.core.urlresolvers import reverse
from django.db.models import Max, Min
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from notecards.models import Deck, Card
from notecards.forms import deckForm, cardForm

import random
import json

import pdb

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
def check_answer(request, deckid):
    deck = get_object_or_404(Deck, pk=deckid)
    cardid = request.POST.get('cardid')
    card = Card.objects.get(pk=cardid)
    front = card.front
    retResp = {'answer': card.back, 'result': 'wrong'}
    userAnswer = request.POST.get('ans')
    answerCards = Card.objects.filter(deck=deck, front=front)
    for ans in answerCards:
        if ans.back == userAnswer:
            if ans.score < 5:
                ans.score += 1
                ans.save()
            retResp['result'] = 'correct'
    if retResp['result'] == 'wrong':
        answerCards.update(score=1)
    jsonResp = json.dumps(retResp)

    return HttpResponse(jsonResp, content_type='application/json')


@login_required
def get_card(request, deckid):
    userid = request.user.id
    user = User.objects.get(pk=userid)
    deck = Deck.objects.filter(pk=deckid, author=user)
    if deck.count() > 0 and deck[0].card_set.count() > 0:
        minScore = deck.aggregate(Min('card__score'))
        minScore = minScore['card__score__min']
        maxScore = deck.aggregate(Max('card__score'))
        maxScore = maxScore['card__score__max']
        rscore = random.randint(minScore, maxScore)
        deck = deck[0]
        cards = deck.card_set.filter(score__lte=rscore)
        rindex = random.randint(0, len(cards) - 1)
        card = cards[rindex]

        context_dict = {'card': card, 'deck': deck, 'mode': 'get_card/'}

        return render(request, 'notecards/drill.html', context_dict)
    else:
        return HttpResponse(status=404)


@login_required
def get_weak_card(request, deckid):
    userid = request.user.id
    user = User.objects.get(pk=userid)
    deck = get_object_or_404(Deck, pk=deckid, author=user)
    cards = deck.card_set.filter(score__lte=3)
    if cards.count() > 0:
        rindex = random.randint(0, len(cards) - 1)
        card = cards[rindex]

        context_dict = {'card': card, 'deck': deck, 'mode': 'gwc/'}

        return render(request, 'notecards/drill.html', context_dict)
    else:
        return HttpResponse(status=404)


def get_deck(request, deckid):
    deck = get_object_or_404(Deck, pk=deckid)
    cards = deck.card_set.all()
    cardsJSON = serializers.serialize('json', cards)

    return HttpResponse(cardsJSON, content_type='application/json')


def get_decks(request):
    if request.method == 'GET':
        page = request.GET.get('page')
        if page:
            page = int(page)
        else:
            page = 1
        if page > 0:
            start = (page - 1) * 50
            end = start + 50
            decks = Deck.objects.filter(published=True).order_by('-dateCreated')[start:end]
            last = len(decks) < 50

            return render(request, 'notecards/decks.html', {'decks': decks,
                                                            'next': page + 1,
                                                            'prev': page - 1,
                                                            'lastpg': last})
        else:
            return HttpResponse('Invalid page number')


def get_user_decks(request, user):
    if request.method == 'GET':
        user = User.objects.get(username=user)
        page = request.GET.get('page')
        if page:
            page = int(page)
        else:
            page = 1
        if page > 0:
            start = (page - 1) * 50
            end = start + 50
            decks = Deck.objects.filter(author=user).order_by('-dateCreated')[start:end]
            last = len(decks) < 50

            return render(request, 'notecards/decks.html', {'decks': decks,
                                                            'next': page + 1,
                                                            'prev': page - 1,
                                                            'lastpg': last})
        else:
            return HttpResponse('Invalid page number')

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
def create_card(request, deckid):
    if request.method == 'POST':
        userID = request.user.id
        user = User.objects.get(pk=userID)
        # redundant filter to make sure user owns the deck
        deck = get_object_or_404(Deck, pk=deckid, author=user)
        form = cardForm(request.POST)
        if form.is_valid():
            front = form.cleaned_data['front']
            back = form.cleaned_data['back']
            card = Card(front=front, back=back, deck=deck)
            card.save()
            content = '<option>{0} -- {1}</option>'.format(front, back)
            return HttpResponse(status=201,
                                content=content,
                                content_type='text/html')
        else:
            return render(request, 'notecards/build.html', {'form': form})


@login_required
def edit_card(request, cardid):
    card = Card.objects.get(pk=cardid)
    userID = request.user.id
    user = User.objects.get(pk=userID)
    if card.deck.author == user:
        if request.method == 'POST':
            front = request.POST.get('editfront')
            back = request.POST.get('editback')
            form = cardForm({'front': front, 'back': back})
            if form.is_valid():
                card.front = form.cleaned_data['front']
                card.back = form.cleaned_data['back']
                card.save()
                content = '<option>{0} -- {1}</option>'.format(
                    card.front,
                    card.back)
                return HttpResponse(status=200,
                                    content=content,
                                    content_type='text/html')
        elif request.method == 'DELETE':
            card.delete()
            return HttpResponse(status=200)


@login_required
def edit_deck(request, deckid):
    userID = request.user.id
    user = User.objects.get(pk=userID)
    deck = get_object_or_404(Deck, author=user, pk=deckid)
    if user == deck.author:
        form = deckForm(request.POST)
        if form.is_valid():
            deck.title = form.cleaned_data['title']
            deck.description = form.cleaned_data['description']
            deck.tags.clear()
            for tag in form.cleaned_data['tags']:
                deck.tags.add(tag)
            deck.save()
            queryParam = '?did={0}'.format(deckid)
            return HttpResponseRedirect(reverse('view_deck') + queryParam)


@login_required
def clone_deck(request):
    deckid = request.GET.get('did')
    userID = request.user.id
    user = User.objects.get(pk=userID)
    deck = Deck.objects.get(pk=deckid)
    if deck.author != user:
        newDeck, created = Deck.objects.get_or_create(author=user,
                                                      title=deck.title)
        if not created:
            return HttpResponse('Error: You already own a deck with '
                                'this title')
        newDeck.slug = deck.slug
        newDeck.description = deck.description,
        newDeck.published = False
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
        url = reverse('view_deck') + '?did=' + str(newDeck.id)
        return HttpResponseRedirect(url)
    else:
        return HttpResponse('Error: You already own this deck')


def view_deck(request):
    deckid = request.GET.get('did')
    deck = Deck.objects.get(pk=deckid)
    deckform = deckForm(instance=deck)
    cardform = cardForm()
    cards = deck.card_set.all()

    context_dict = {'deckform': deckform,
                    'cardform': cardform,
                    'cards': cards,
                    'deck': deck}

    return render(request, 'notecards/view_deck.html', context_dict)


@login_required
def delete_deck(request):
    userID = request.user.id
    user = User.objects.get(pk=userID)
    if request.method == 'POST':
        deckID = request.POST.get('did')
        deck = get_object_or_404(Deck, pk=deckID)
        if deck.author == user:
            deck.delete()
            return HttpResponseRedirect(reverse('get_user_decks',
                                        kwargs={'user': user.username}))
        else:
            return HttpResponse(status=404)

    if request.method == 'GET':
        deckID = request.GET.get('did')
        deck = get_object_or_404(Deck, pk=deckID)
        if deck.author == user:
            context_dict = {'deck': deck}
            return render(request,
                          'notecards/delete_confirm.html',
                          context_dict)
        else:
            return HttpResponse(status=404)


@login_required
def publish_deck(request):
    userID = request.user.id
    user = User.objects.get(pk=userID)
    if request.method == 'POST':
        deckID = request.POST.get('did')
        deck = get_object_or_404(Deck, pk=deckID)
        if deck.author == user:
            deck.published = not deck.published
            deck.save()
            return HttpResponse(status=200)
    return HttpResponse(status=404)

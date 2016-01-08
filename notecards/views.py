from django.shortcuts import render, get_object_or_404
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


def index(request):
    '''
    Simply returns the home page
    '''
    return render(request, 'notecards/index.html', {})


@login_required
def check_answer(request, deckid):
    '''
    Checks whether the user's answer for a flashcard is correct or not.
    If not, the card's score is set to 0. If it is, a point is added up
    to a maximum of 5 points.
    Returns JSON data indicating whether the answer was wrong or correct.
    '''
    # Get information about the card presented to the user
    deck = get_object_or_404(Deck, pk=deckid)
    cardid = request.POST.get('cardid')
    card = Card.objects.get(pk=cardid)
    front = card.front
    retResp = {'answer': card.back, 'result': 'wrong'}
    # Get user's answer as well as all cards they might have possibly
    # thought they were being presented with. We give the user the
    # benefit of a doubt.
    userAnswer = request.POST.get('ans')
    answerCards = Card.objects.filter(deck=deck, front=front)
    for ans in answerCards:
        # For any card that matches the answer given, add 1 point
        if ans.back == userAnswer:
            if ans.score < 5:
                ans.score += 1
                ans.save()
            retResp['result'] = 'correct'
    if retResp['result'] == 'wrong':
        # If user's answer didn't match anything, then reset the
        # presented card's points
        answerCards.update(score=1)
    jsonResp = json.dumps(retResp)

    return HttpResponse(jsonResp, content_type='application/json')


@login_required
def get_card(request, deckid):
    '''
    Fetches a card to be presented to the user
    '''
    # Get information necessary to determine which deck to pull from
    userid = request.user.id
    user = User.objects.get(pk=userid)
    deck = Deck.objects.filter(pk=deckid, author=user)
    # Make sure deck actually has cards in it
    if deck.count() > 0 and deck[0].card_set.count() > 0:
        # Randomly select a card to draw, biasing towards weaker cards
        minScore = deck.aggregate(Min('card__score'))
        minScore = minScore['card__score__min']
        maxScore = deck.aggregate(Max('card__score'))
        maxScore = maxScore['card__score__max']
        rscore = random.randint(minScore, maxScore)
        deck = deck[0]
        cards = deck.card_set.filter(score__lte=rscore)
        rindex = random.randint(0, len(cards) - 1)
        card = cards[rindex]

        # 'mode' is used in the template to build the URL for fetching
        # the next card.
        context_dict = {'card': card, 'deck': deck, 'mode': 'get_card/'}

        return render(request, 'notecards/drill.html', context_dict)
    else:
        return HttpResponse(status=404)


@login_required
def get_weak_card(request, deckid):
    '''
    Fetches a card with a score of 3 or less to be presented to the user.
    '''
    userid = request.user.id
    user = User.objects.get(pk=userid)
    deck = get_object_or_404(Deck, pk=deckid, author=user)
    cards = deck.card_set.filter(score__lte=3)
    if cards.count() > 0:
        # If we have any weak cards then draw a random one
        rindex = random.randint(0, len(cards) - 1)
        card = cards[rindex]

        # 'mode' is used in the template to build the URL for fetching
        # the next card
        context_dict = {'card': card, 'deck': deck, 'mode': 'gwc/'}

        return render(request, 'notecards/drill.html', context_dict)
    else:
        return HttpResponse(status=404)


def get_deck(request, deckid):
    '''
    Returns all cards in a deck in JSON format
    '''
    deck = get_object_or_404(Deck, pk=deckid)
    cards = deck.card_set.all()
    cardsJSON = serializers.serialize('json', cards)

    return HttpResponse(cardsJSON, content_type='application/json')


def get_decks(request):
    '''
    Fetches a maximum of 50 decks to display to the user in order of
    creation date.
    Returns a page populated with rows of said decks.
    '''
    page = request.GET.get('page')
    if page:
        page = int(page)
    else:
        # Default to 1st page if no page number present in GET request
        page = 1
    if page > 0:
        start = (page - 1) * 50
        end = start + 50
        # Only fetch published decks
        decks = Deck.objects.filter(published=True).order_by('-dateCreated')[start:end]
        # last is a boolean that tells the template not to render the
        # 'next' button if we're already on the last page as indicated
        # by getting fewer than 50 decks in the query
        last = len(decks) < 50

        return render(request, 'notecards/decks.html', {'decks': decks,
                                                        'next': page + 1,
                                                        'prev': page - 1,
                                                        'lastpg': last})
    else:
        return HttpResponse('Invalid page number')


def get_user_decks(request, user):
    '''
    Fetches a maximum of 50 decks to display to the user in order of
    creation date. The only decks returned are those belonging to the user.
    Returns a page populated with rows of said decks.
    '''
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
    '''
    GET: Present the user with the form to create a new deck.
    POST: Process user input and create the new deck.
    '''
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
        else:
            return render(request, 'notecards/create_deck.html', {'form': form})
    form = deckForm()
    return render(request, 'notecards/create_deck.html', {'form': form})


@login_required
def create_card(request, deckid):
    '''
    Accepts an AJAX POST request to create a new card.
    Returns card information in HTML to be inserted into the page.
    '''
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
            # Card goes into a select box so we use the <option> tag
            content = '<option>{0} -- {1}</option>'.format(front, back)
            return HttpResponse(status=201,
                                content=content,
                                content_type='text/html')
        else:
            return render(request, 'notecards/build.html', {'form': form})


@login_required
def edit_card(request, cardid):
    '''
    POST: Replaces a card's information with new information from the user.
          Returns new card info in HTML form to be appended into the page.
    DELETE: Deletes the card from the deck.
    '''
    card = Card.objects.get(pk=cardid)
    userID = request.user.id
    user = User.objects.get(pk=userID)
    if card.deck.author == user:
        if request.method == 'POST':
            # Replace the old card info with new info
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
    '''
    Replaces deck information with new information submitted by user.
    '''
    userID = request.user.id
    user = User.objects.get(pk=userID)
    # Make sure user owns deck
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
    '''Creates a copy of a user's deck for another user to own.'''
    deckid = request.GET.get('did')
    userID = request.user.id
    user = User.objects.get(pk=userID)
    deck = Deck.objects.get(pk=deckid)
    # Make sure user isn't trying to clone their own deck
    if deck.author != user:
        newDeck, created = Deck.objects.get_or_create(author=user,
                                                      title=deck.title)
        # Check to make sure that user doesn't already have a deck the
        # same title
        if not created:
            return HttpResponse('Error: You already own a deck with '
                                'this title')
        # Copy the deck
        newDeck.slug = deck.slug
        newDeck.description = deck.description,
        newDeck.published = False
        newDeck.save()
        # Copy the tags
        tags = deck.tags.names()
        for tag in tags:
            newDeck.tags.add(tag)
        newDeck.save()
        # Copy the cards
        for card in deck.card_set.all():
            newCard = Card(front=card.front,
                           back=card.back,
                           deck=newDeck,
                           score=0)
            newCard.save()
        # Redirect user to their newly cloned deck
        url = reverse('view_deck') + '?did=' + str(newDeck.id)
        return HttpResponseRedirect(url)
    else:
        return HttpResponse('Error: You already own this deck')


def view_deck(request):
    '''
    Returns a page with all the information about a deck
    '''
    deckid = request.GET.get('did')
    deck = Deck.objects.get(pk=deckid)
    # deck form is pre-filled with deck info
    deckform = deckForm(instance=deck)
    # card form is empty since it's used to add new cards
    cardform = cardForm()
    cards = deck.card_set.all()

    context_dict = {'deckform': deckform,
                    'cardform': cardform,
                    'cards': cards,
                    'deck': deck}

    return render(request, 'notecards/view_deck.html', context_dict)


@login_required
def delete_deck(request):
    '''
    POST: Deletes the deck.
    GET: Returns a page asking user to confirm the deletion.
    '''
    userID = request.user.id
    user = User.objects.get(pk=userID)
    if request.method == 'POST':
        deckID = request.POST.get('did')
        deck = get_object_or_404(Deck, pk=deckID)
        if deck.author == user:
            deck.delete()
            # Return user to view all their remaining decks
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
    '''
    Makes a deck visable or invisible to other users when browsing decks.
    '''
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

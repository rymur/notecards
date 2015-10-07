from django.test import TestCase
from django.core.urlresolvers import reverse
import factory
from factory import fuzzy
import random

from notecards.models import Deck, Card
from notecards.forms import deckForm
from django.contrib.auth.models import User


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user%d' % n)
    password = factory.Sequence(lambda n: 'pass%d' % n)


class DeckFactory(factory.DjangoModelFactory):
    class Meta:
        model = Deck

    author = factory.SubFactory(UserFactory)
    title = fuzzy.FuzzyText()
    description = fuzzy.FuzzyText()


class CardFactory(factory.DjangoModelFactory):
    class Meta:
        model = Card

    front = fuzzy.FuzzyText()
    back = fuzzy.FuzzyText()
    deck = factory.SubFactory(DeckFactory)
    score = random.randint(-20, 10)


class TestNotecardViews(TestCase):

    def setUp(self):
        User.objects.create_user(username='auser', password='apass')
        User.objects.create_user(username='buser', password='bpass')

    def test_get_card(self):
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        user = User.objects.get(username='auser')
        deck = DeckFactory.create(title='test deck', author=user)
        CardFactory.create_batch(10, deck=deck)
        resp = self.client.get('/notecards/get_card/test-deck', follow=True)

        self.assertContains(resp, 'score', 1)
        self.assertContains(resp, 'front', 1)
        self.assertContains(resp, 'back', 1)

    def test_get_deck(self):
        deck = DeckFactory(title='test deck')
        for i in range(0, 10):
            CardFactory(deck=deck)

        resp = self.client.get('/notecards/get_deck/test-deck', follow=True)

        self.assertContains(resp, 'score', 10)

    def test_get_all_decks(self):
        DeckFactory.create_batch(5)

        resp = self.client.get(reverse('get_all_decks'))
        self.assertContains(resp, 'title', 5)

    def test_get_user_deck(self):
        user = User.objects.get(username='auser')
        for i in range(0, 10):
            DeckFactory.create(author=user)

        userb = User.objects.get(username='buser')
        for i in range(0, 10):
            DeckFactory.create(author=userb)

        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        resp = self.client.get('/notecards/get_user_decks/auser/')

        self.assertContains(resp, 'author', 10)

    def test_add_score_to_card(self):
        card = CardFactory(score=0)
        card.score += 1
        card.save()
        self.assertEqual(1, card.score)

    def test_check_answer(self):
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        user = User.objects.get(username='auser')

        deck = DeckFactory.create(author=user, title='test-deck')
        card = CardFactory.create(front='test',
                                  back='tset',
                                  deck=deck,
                                  score=0)
        # test correct answer
        data = {'front': card.front,
                'ans': 'tset',
                }
        resp = self.client.post(reverse('check_answer',
                                kwargs={'title_slug': 'test-deck'}),
                                data=data)
        card = Card.objects.get(id=card.id)
        self.assertContains(resp, 'correct', 1)
        self.assertEqual(card.score, 1)

        # test wrong answer
        data = {
            'front': card.front,
            'ans': 'wrong',
        }
        resp = self.client.post(reverse('check_answer',
                                kwargs={'title_slug': 'test-deck'}),
                                data=data)
        card = Card.objects.get(id=card.id)
        self.assertContains(resp, 'wrong', 1)
        self.assertEqual(card.score, 0)

        # test multiple cards
        card2 = CardFactory(deck=deck, front='test', score=0)
        card3 = CardFactory(deck=deck, front='notest', score=0)

        resp = self.client.post(reverse('check_answer',
                                kwargs={'title_slug': 'test-deck'}),
                                data=data)
        card = Card.objects.get(id=card.id)
        self.assertEqual(card.score, -1)
        card2 = Card.objects.get(id=card2.id)
        self.assertEqual(card2.score, -1)
        card3 = Card.objects.get(id=card3.id)
        self.assertEqual(card3.score, 0)

    def test_deckForm(self):
        form = deckForm({'title': 'Test Deck',
                        'description': 'The description'})
        self.assertTrue(form.is_valid())

    def test_create_deck(self):
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        user = User.objects.get(username='auser')

        resp = self.client.post(reverse('create_deck'),
                                {'title': 'Test Deck',
                                 'description': 'The description'})
        self.assertContains(resp, 'success', 1)
        deck = Deck.objects.get(title='Test Deck')
        self.assertEqual(deck.author, user)
        self.assertEqual(deck.description, 'The description')
        self.assertEqual(deck.numCards, 0)
        self.assertEqual(deck.slug, 'test-deck')

        # test GET
        resp = self.client.get(reverse('create_deck'))
        self.assertContains(resp, 'failed', 1)

    def test_create_card(self):
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        user = User.objects.get(username='auser')

        deck = DeckFactory(author=user)
        url = '/notecards/create_card/' + deck.slug + '/'
        resp = self.client.post(url,
                                {'front': 'question',
                                 'back': 'answer'})
        self.assertContains(resp, 'success', 1)
        card = Card.objects.get(front='question')
        self.assertEqual(card.back, 'answer')
        self.assertEqual(card.deck, deck)
        self.assertEqual(card.score, 0)

    def test_clone_deck(self):
        auser = User.objects.get(username='auser')
        buser = User.objects.get(username='buser')
        decka = DeckFactory(author=auser, title='test-deck')
        for i in range(0, 10):
            CardFactory.create(deck=decka)

        # test that clone fails with same user
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        resp = self.client.post(reverse('clone_deck'),
                                data={'deck': 'test-deck'})
        self.assertContains(resp, 'Error: You', 1)
        self.client.logout()

        # test that clone succeeds with different user
        b = self.client.login(username='buser', password='bpass')
        self.assertTrue(b)
        resp = self.client.post(reverse('clone_deck'),
                                data={'deck': 'test-deck'})
        self.assertEqual(resp.status_code, 201)
        bdeck = Deck.objects.get(author=buser, title='test-deck')
        self.assertEqual(10, len(bdeck.card_set.all()))

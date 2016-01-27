from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
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

    def test_deck_validation(self):
        # tests that no user can create more than 100 decks
        auser = User.objects.get(username='auser')
        buser = User.objects.get(username='buser')
        for i in range(0, 100):
            DeckFactory(author=auser)
        self.assertEqual(100, Deck.objects.filter(author=auser).count())
        with self.assertRaises(ValidationError):
            DeckFactory(author=auser)
        try:
            DeckFactory(author=buser)
        except ValidationError:
            self.fail("ValidationError raised on user"
                      "with less than 50 decks")

        # tests that user cannot create multiple decks with the same title
        DeckFactory(author=buser, title='title')
        with self.assertRaises(IntegrityError):
            DeckFactory(author=buser, title='title')

    def test_deck_model_numCards(self):
        # test that cards are correclty associated with a deck
        deck = DeckFactory()
        for i in range(0, 10):
            CardFactory(deck=deck)
        self.assertEqual(10, deck.numCards)

    def test_add_score_to_card(self):
        # test adding a point to a card
        card = CardFactory(score=0)
        card.score += 1
        card.save()
        self.assertEqual(1, card.score)

    def test_get_card(self):
        # test that a user can fetch a card from the get_card view
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        user = User.objects.get(username='auser')
        deck = DeckFactory.create(title='test deck', author=user)
        CardFactory.create_batch(10, deck=deck)
        resp = self.client.get(reverse('get_card',
                               kwargs={'deckid': deck.id}))

        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context['deck'], deck)

        # test that buser can't use get_card for auser's cards
        self.client.logout()
        b = self.client.login(username='buser', password='bpass')
        self.assertTrue(b)
        resp = self.client.get(reverse('get_card',
                               kwargs={'deckid': deck.id}))

        self.assertEquals(resp.status_code, 404)

    def test_get_weak_card(self):
        # test user can draw a weak card from get_weak_card view
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        user = User.objects.get(username='auser')
        deck = DeckFactory(author=user)
        for i in range(0, 10):
            r = random.randint(1, 3)
            CardFactory(deck=deck, score=r)
        for i in range(0, 10):
            r = random.randint(4, 5)
            CardFactory(deck=deck, score=r)
        for i in range(0, 30):
            resp = self.client.get(reverse('get_weak_card',
                                   kwargs={'deckid': deck.id}))
            self.assertLess(resp.context['card'].score, 4)

        # Test user can't get other user's cards
        self.client.logout()
        self.client.login(username='buser', password='bpass')
        resp = self.client.get(reverse('get_weak_card',
                               kwargs={'deckid': deck.id}))

    def test_get_deck(self):
        # get test that the get_deck view correctly returns the details
        # of a deck
        deck = DeckFactory(title='test deck')
        for i in range(0, 10):
            CardFactory(deck=deck)

        resp = self.client.get(reverse('get_deck',
                               kwargs={'deckid': deck.id}))

        self.assertContains(resp, 'score', 10)

    def test_get_decks(self):
        DeckFactory.create_batch(125)

        # test getting first page without specifying page number
        resp = self.client.get(reverse('decks'))
        self.assertEquals(resp.context['decks'].count(), 50)

        # test getting subsequent pages
        resp = self.client.get(reverse('decks'), {'page': 2})
        self.assertEquals(resp.context['decks'].count(), 50)
        resp = self.client.get(reverse('decks'), {'page': 3})
        self.assertEquals(resp.context['decks'].count(), 25)

    def test_get_user_deck(self):
        user = User.objects.get(username='auser')
        for i in range(0, 10):
            DeckFactory.create(author=user)

        userb = User.objects.get(username='buser')
        for i in range(0, 75):
            DeckFactory.create(author=userb)

        # Test from same user that deck belongs to
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        resp = self.client.get(reverse('get_user_decks',
                               kwargs={'user': 'auser'}))
        self.assertEquals(resp.context['decks'].count(), 10)

        # Test from different user than deck belongs to
        resp = self.client.get(reverse('get_user_decks',
                               kwargs={'user': 'buser'}))
        self.assertEquals(resp.context['decks'].count(), 50)

        # Test different user requesting second page
        resp = self.client.get(reverse('get_user_decks',
                               kwargs={'user': 'buser'}),
                               {'page': 2})
        self.assertEquals(resp.context['decks'].count(), 25)

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
        data = {'cardid': card.id,
                'ans': 'tset',
                }
        resp = self.client.post(reverse('check_answer',
                                kwargs={'deckid': deck.id}),
                                data=data)
        card = Card.objects.get(id=card.id)
        self.assertContains(resp, 'correct', 1)
        self.assertEqual(card.score, 1)

        resp = self.client.post(reverse('check_answer',
                                kwargs={'deckid': deck.id}),
                                data=data)
        card = Card.objects.get(id=card.id)
        self.assertContains(resp, 'correct', 1)
        self.assertEqual(card.score, 2)

        resp = self.client.post(reverse('check_answer',
                                kwargs={'deckid': deck.id}),
                                data=data)
        card = Card.objects.get(id=card.id)
        self.assertContains(resp, 'correct', 1)
        self.assertEqual(card.score, 3)

        # test wrong answer
        data = {
            'cardid': card.id,
            'ans': 'wrong',
        }
        resp = self.client.post(reverse('check_answer',
                                kwargs={'deckid': deck.id}),
                                data=data)
        card = Card.objects.get(id=card.id)
        self.assertContains(resp, 'wrong', 1)
        self.assertEqual(card.score, 1)

        # test multiple cards
        card2 = CardFactory(deck=deck, front='test', score=0)
        card3 = CardFactory(deck=deck, front='notest', score=0)

        resp = self.client.post(reverse('check_answer',
                                kwargs={'deckid': deck.id}),
                                data=data)
        card = Card.objects.get(id=card.id)
        self.assertEqual(card.score, 1)
        card2 = Card.objects.get(id=card2.id)
        self.assertEqual(card2.score, 1)
        card3 = Card.objects.get(id=card3.id)
        self.assertEqual(card3.score, 0)

    def test_deckForm(self):
        # save without tags
        form = deckForm({'title': 'Test Deck',
                        'description': 'The description',
                         })
        self.assertTrue(form.is_valid())

        # save with tags
        form = deckForm({'title': 'Test Deck 2',
                         'description': 'Description 2',
                         'tags': 'testing'})
        self.assertTrue(form.is_valid())

    def test_create_deck(self):
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        user = User.objects.get(username='auser')

        # test POST
        self.client.post(reverse('create_deck'),
                         {'title': 'Test Deck',
                          'description': 'The description',
                          'tags': 'test, test2'},
                         follow=True)
        deck = Deck.objects.get(title='Test Deck')
        self.assertEqual(deck.author, user)
        self.assertEqual(deck.description, 'The description')
        self.assertEqual(deck.slug, 'test-deck')
        self.assertCountEqual(deck.tags.names(), ['test', 'test2'])

        # Test GET
        resp = self.client.get(reverse('create_deck'))
        self.assertEqual(resp.status_code, 200)

    def test_create_card(self):
        # Test that user can create a card using the create_card view

        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        user = User.objects.get(username='auser')

        deck = DeckFactory(author=user)
        resp = self.client.post(reverse('create_card',
                                kwargs={'deckid': deck.id}),
                                {'front': 'question',
                                 'back': 'answer'})
        self.assertEqual(resp.status_code, 201)
        card = Card.objects.get(front='question')
        self.assertEqual(card.back, 'answer')
        self.assertEqual(card.deck, deck)
        self.assertEqual(card.score, 0)
        expected = '<option>question -- answer</option>'
        self.assertContains(resp, expected, 1, status_code=201)

    def test_edit_deck(self):
        auser = User.objects.get(username='auser')
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        deck = DeckFactory(author=auser)
        for i in range(0, 10):
            CardFactory(deck=deck)

        # Test that same user can edit their own deck
        resp = self.client.post(reverse('edit_deck',
                                kwargs={'deckid': deck.id}),
                                {'title': 'title',
                                 'description': 'description',
                                 'tags': 'tag1, tag2'})
        self.assertEquals(resp.status_code, 302)
        deck = Deck.objects.get(pk=deck.id)
        self.assertEquals(deck.title, 'title')
        self.assertEquals(deck.description, 'description')
        self.assertCountEqual(deck.tags.names(), ['tag1', 'tag2'])
        self.assertEquals(deck.card_set.count(), 10)

        # Test that a different user cannot edit another user's deck
        self.client.logout()
        self.client.login(username='buser', password='bpass')
        resp = self.client.post(reverse('edit_deck',
                                kwargs={'deckid': deck.id}),
                                data={'title': 'title2',
                                      'description': 'description2',
                                      'tags': 'tag3, tag4'})
        self.assertEquals(resp.status_code, 404)
        self.assertEquals(deck.title, 'title')
        self.assertEquals(deck.description, 'description')
        self.assertCountEqual(deck.tags.names(), ['tag1', 'tag2'])
        self.assertEquals(deck.card_set.count(), 10)

    def test_clone_deck(self):
        auser = User.objects.get(username='auser')
        buser = User.objects.get(username='buser')
        decka = DeckFactory(author=auser, title='test-deck')
        for i in range(0, 10):
            CardFactory.create(deck=decka)
        decka.tags.add('test', 'atag')

        # test that clone fails with same user
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        resp = self.client.get(reverse('clone_deck'),
                               {'did': decka.id})
        self.assertContains(resp, 'Error: You', 1)
        self.client.logout()

        # test that clone succeeds with different user
        b = self.client.login(username='buser', password='bpass')
        self.assertTrue(b)
        resp = self.client.get(reverse('clone_deck'),
                               {'did': decka.id})
        self.assertEqual(resp.status_code, 302)
        bdeck = Deck.objects.get(author=buser, title='test-deck')
        self.assertEqual(10, len(bdeck.card_set.all()))
        self.assertCountEqual(bdeck.tags.names(), ['test', 'atag'])

        # test that clone fails with already owned deck
        resp = self.client.get(reverse('clone_deck'),
                               {'did': decka.id})
        self.assertContains(resp, 'with this title', 1)

    def delete_deck(self):
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)

        # TEST POST

        # Test that delete_deck works on same user's decks
        auser = User.objects.get(username='auser')
        deck1 = DeckFactory(author=auser)
        deck2 = DeckFactory(author=auser)
        self.assertEquals(2, Deck.objects.all().count())
        resp = self.client.post(reverse('delete_deck'),
                                {'did': deck1.id})
        self.assertEquals(302, resp.status_code)
        self.assertEquals(1, Deck.objects.all().count())
        resp = self.client.post(reverse('delete_deck'),
                                {'did': deck2.id})
        self.assertEquals(302, resp.status_code)
        self.assertEquals(0, Deck.objects.all().count())

        # Test that delete_deck fails on different user's decks
        buser = User.objects.get(username='buser')
        deckb = DeckFactory(author=buser)
        resp = self.client.post(reverse('delete_deck'),
                                {'did': deckb.id})
        self.assertEquals(404, resp.status_code)

        # TEST GET

        # Requesting user owns deck
        decka = DeckFactory(author=auser)
        resp = self.client.get(reverse('delete_deck'),
                               {'did': decka.id})
        self.assertEquals(200, resp.status_code)
        self.assertContains(resp, 'Are you sure', 1)

        # Requesting user does not own deck
        resp = self.client.get(reverse('delete_deck'),
                               {'did': deckb.id})
        self.assertEquals(404, resp.status_code)

    def test_publish_deck(self):
        a = self.client.login(username='auser', password='apass')
        self.assertTrue(a)
        auser = User.objects.get(username='auser')
        deck = DeckFactory(author=auser)
        self.assertTrue(deck.published)

        # unpublish
        resp = self.client.post(reverse('publish'),
                                {'did': deck.id})
        self.assertEquals(200, resp.status_code)
        deck = Deck.objects.get(pk=deck.id)
        self.assertFalse(deck.published)

        # republish
        resp = self.client.post(reverse('publish'),
                                {'did': deck.id})
        self.assertEquals(200, resp.status_code)
        deck = Deck.objects.get(pk=deck.id)
        self.assertTrue(deck.published)

        # test that a user can't publish someone else's deck
        self.client.logout()
        b = self.client.login(username='buser', password='bpass')
        self.assertTrue(b)
        resp = self.client.post(reverse('publish'),
                                {'did': deck.id})
        self.assertEquals(404, resp.status_code)

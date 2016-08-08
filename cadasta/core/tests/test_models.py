import random
from django.db.models import SlugField, CharField, Model
from django.test import TestCase
from ..models import RandomIDModel, SlugModel


class MyRandomIdModel(RandomIDModel):
    class Meta:
        app_label = 'core'


class RandomIDModelTest(TestCase):
    abstract_model = RandomIDModel

    def test_save(self):
        instance = MyRandomIdModel()
        instance.save()
        assert instance.id is not None

    def test_duplicate_ids(self):
        random.seed(a=10)
        instance1 = MyRandomIdModel()
        instance1.save()
        random.seed(a=10)
        instance2 = MyRandomIdModel()
        instance2.save()
        assert instance1.id != instance2.id


class MySlugModel(SlugModel, Model):
    name = CharField(max_length=100)
    slug = SlugField(max_length=50, unique=True)

    class Meta:
        app_label = 'core'


class SlugModelTest(TestCase):
    name = CharField(max_length=200)
    abstract_model = SlugModel

    def test_save(self):
        instance = MySlugModel()
        instance.name = 'Test Name'
        instance.save()

        instance.refresh_from_db()
        assert instance.slug == 'test-name'

    def test_save_slug_is_set(self):
        instance = MySlugModel()
        instance.name = 'Test Name'
        instance.slug = 'slug'
        instance.save()

        instance.refresh_from_db()
        assert instance.slug == 'slug'

    def test_duplicate_slug(self):
        instance1 = MySlugModel()
        instance1.name = 'Test Name'
        instance1.save()

        instance2 = MySlugModel()
        instance2.name = 'Test Name'
        instance2.save()

        instance1.refresh_from_db()
        instance2.refresh_from_db()
        assert instance1.slug != instance2.slug
        assert instance2.slug == 'test-name-1'

    def test_duplicate_slug_is_set(self):
        instance1 = MySlugModel()
        instance1.name = 'Test Name'
        instance1.save()

        instance2 = MySlugModel()
        instance2.name = 'Some Name'
        instance2.slug = instance1.slug
        instance2.save()

        instance1.refresh_from_db()
        instance2.refresh_from_db()
        assert instance1.slug != instance2.slug
        assert instance2.slug == 'test-name-1'

    def test_create_with_duplicate_slug(self):
        instance1 = MySlugModel()
        instance1.name = 'Test Name'
        instance1.save()

        instance2 = MySlugModel(
            name='Some Name',
            slug=instance1.slug,
        )
        instance2.save()
        assert instance1.slug != instance2.slug
        assert instance2.slug == 'test-name-1'

    def test_duplicate_slug_100_times(self):
        for i in range(0, 101):
            instance = MySlugModel()
            instance.name = ("Test Name")
            instance.save()

        assert MySlugModel.objects.count() == 101
        assert instance.slug == 'test-name-100'

    def test_keep_slug(self):
        instance = MySlugModel()
        instance.name = 'Test Name'
        instance.save()

        instance.name = 'Other Name'
        instance.save()

        instance.refresh_from_db()
        assert instance.name == 'Other Name'
        assert instance.slug == 'test-name'

    def test_create_with_long_name(self):
        instance = MySlugModel()
        instance.name = ('Very Long Name For The Purposes of '
                         'Testing That Slug Truncation Functions Correctly')
        instance.save()

        assert len(instance.slug) == 50

    def test_duplicate_slug_long_name(self):
        instance1 = MySlugModel()
        instance1.name = ('Very Long Name For The Purposes of '
                          'Testing That Slug Truncation Functions Correctly')
        instance1.save()

        instance2 = MySlugModel()
        instance2.name = ('Very Long Name For The Purposes of '
                          'Testing That Slug Truncation Functions Correctly')
        instance2.save()

        instance1.refresh_from_db()
        instance2.refresh_from_db()
        assert instance1.slug != instance2.slug
        assert instance2.slug[-2:] == '-1'
        print(instance1.slug)
        print(instance2.slug)

    def test_duplicate_slug_long_name_100_times(self):
        for i in range(0, 101):
            instance = MySlugModel()
            instance.name = ('Very Long Name For The Purposes of Testing '
                             'That Slug Truncation Functions Correctly')
            instance.save()

        assert MySlugModel.objects.count() == 101
        assert instance.slug[-4:] == '-100'

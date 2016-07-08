import itertools
from django.utils.text import slugify
from django.db import models

from .util import random_id, ID_FIELD_LENGTH


class RandomIDModel(models.Model):
    id = models.CharField(primary_key=True, max_length=ID_FIELD_LENGTH)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            kwargs['force_insert'] = True

            ok = False
            while not ok:
                self.id = random_id()

                if not type(self).objects.filter(pk=self.id).exists():
                    ok = True
                    super(RandomIDModel, self).save(*args, **kwargs)

        else:
            super(RandomIDModel, self).save(*args, **kwargs)


class SlugModel:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_slug = self.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)

        orig = self.slug

        if not self.id or self.__original_slug != self.slug:
            for x in itertools.count(1):
                if not type(self).objects.filter(slug=self.slug).exists():
                    break
                self.slug = '{}-{}'.format(orig, x)

        self.__original_slug = self.slug

        return super().save(*args, **kwargs)

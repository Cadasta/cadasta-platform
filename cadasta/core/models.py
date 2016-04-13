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

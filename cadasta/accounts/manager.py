from django.db.models import Q
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.utils.translation import ugettext as _


class UserManager(DjangoUserManager):
    def get_from_username_or_email(self, identifier=None):
        users = self.filter(Q(username=identifier) | Q(email=identifier))
        users_count = len(users)

        if users_count == 1:
            return users[0]

        if users_count == 0:
            error = _(
                "User with username or email {} does not exist"
            ).format(identifier)
            raise self.model.DoesNotExist(error)
        else:
            error = _(
                "More than one user found for username or email {}"
            ).format(identifier)
            raise self.model.MultipleObjectsReturned(error)

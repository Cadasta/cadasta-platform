from tutelary.models import Role


class SuperUserCheck:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._su_role = None

    def is_superuser(self, user):
        if not hasattr(self, 'su_role'):
            self.su_role = Role.objects.get(name='superuser')

        return any([isinstance(pol, Role) and pol == self.su_role
                    for pol in user.assigned_policies()])

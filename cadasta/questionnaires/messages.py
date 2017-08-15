from django.utils.translation import ugettext as _

QUESTIONNAIRE_VIEW = _("You don't have permission to view a questionnaire "
                       "of this project")
QUESTIONNAIRE_ADD = _("You don't have permission to add a questionnaire to "
                      "this project")
QUESTIONNAIRE_EDIT = _("You don't have permission to edit the "
                       "questionnaire of this project")

MISSING_RELEVANT = _("Unable to assign question group to model entitity. Make "
                     "sure to add a 'relevant' clause to the question group "
                     "definition when adding more than one question group for "
                     "a model entity.")
INVALID_ACCURACY = _("Accuracy threshold must be positive float.")

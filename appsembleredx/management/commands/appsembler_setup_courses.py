"""
Run all pre-/ and publish handlers to set up existing
courses.  Doesn't actually publish the course
"""
import logging
from django.core.management import BaseCommand, CommandError
from optparse import make_option
from textwrap import dedent

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator

from contentstore.management.commands.prompt import query_yes_no

from xmodule.modulestore.django import modulestore

from appsembleredx import signals


class Command(BaseCommand):
    """
    Command to run all appsembleredx per-course setup

    Examples:

        ./manage.py appsembler_setup_courses <course_id_1> <course_id_2> - sets up courses with keys course_id_1 and course_id_2
        ./manage.py appsembler_setup_courses --all - sets up all available courses
    """
    help = dedent(__doc__)

    can_import_settings = True

    args = "<course_id course_id ...>"

    all_option = make_option('--all',
                             action='store_true',
                             dest='all',
                             default=False,
                             help='Reindex all courses')

    option_list = BaseCommand.option_list + (all_option,)

    CONFIRMATION_PROMPT = u"Setting up all courses might be a time consuming operation. Do you want to continue?"

    def _parse_course_key(self, raw_value):
        """ Parses course key from string """
        try:
            result = CourseKey.from_string(raw_value)
        except InvalidKeyError:
            raise CommandError("Invalid course_key: '%s'." % raw_value)

        if not isinstance(result, CourseLocator):
            raise CommandError(u"Argument {0} is not a course key".format(raw_value))

        return result

    def handle(self, *args, **options):
        """
        By convention set by Django developers, this method actually executes command's actions.
        So, there could be no better docstring than emphasize this once again.
        """
        all_option = options.get('all', False)

        if len(args) == 0 and not all_option:
            raise CommandError(u"appsembler_setup_courses requires one or more arguments: <course_id>")

        store = modulestore()

        if all_option:
           # if reindexing is done during devstack setup step, don't prompt the user
            if query_yes_no(self.CONFIRMATION_PROMPT, default="no"):
                # in case of --all, get the list of course keys from all courses
                # that are stored in the modulestore
                course_keys = [course.id for course in modulestore().get_courses()]
            else:
                return
        else:
            # in case course keys are provided as arguments
            course_keys = map(self._parse_course_key, args)

        for course_key in course_keys:
        	# call functions that are normally signal handlers 
			signals._default_mode_on_course_publish(store.__class__, course_key)
			signals._change_cert_defaults_on_pre_publish(store.__class__, course_key)
			signals._enable_self_generated_certs_on_publish(store.__class__, course_key)
			signals._make_default_active_certificate(store.__class__, course_key)


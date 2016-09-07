"""
Signal handler for setting default course mode expiration dates
"""
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler, modulestore

from course_modes.models import CourseMode, CourseModeExpirationConfig

from appsembleredx.app_settings import DEFAULT_COURSE_MODE_SLUG, mode_name_from_slug


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    creates a CourseMode in the default mode
    """
    try:
        default_mode = CourseMode.objects.get(course_id=course_key, mode_slug=DEFAULT_COURSE_MODE_SLUG)
    except ObjectDoesNotExist:
        default_mode = CourseMode(course_id=course_key, mode_slug=DEFAULT_COURSE_MODE_SLUG,
                                  mode_display_name=mode_name_from_slug)
        default_mode.save()
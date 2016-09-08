"""
Signal handler for setting default course mode expiration dates
"""
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler, modulestore

from course_modes.models import CourseMode, CourseModeExpirationConfig

from appsembleredx.app_settings import (DEFAULT_COURSE_MODE_SLUG, 
    mode_name_from_slug, USE_OPEN_ENDED_CERTS_DEFAULTS)


@receiver(SignalHandler.course_published)
def _default_mode_on_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
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


@receiver(SignalHandler.pre_publish)
def _change_cert_defaults_on_pre_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been pre-published in Studio and
    updates certificate_display_behavior and ...
    """
    # has to be done this way since it's not possible to monkeypatch the default attrs on the 
    # CourseFields fields
    # TODO: cache so we know we've done this for this course.  We do want Studio user to be able
    # to change these defaults so we only want to do this once
    if not USE_OPEN_ENDED_CERTS_DEFAULTS:
        return

    store = modulestore()
    course = store.get_course(course_key)
    course.certificates_display_behavior = 'early_with_info'
    course.certificates_show_before_end = True
    course.cert_html_view_enabled = True
    course.save()
    store.update_item(course, course._edited_by)

@receiver(SignalHandler.course_published)
def _activate_default_cert_on_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Activate a default HTML certificate on course publish
    """
    if not USE_OPEN_ENDED_CERTS_DEFAULTS:
        return

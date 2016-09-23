"""
Signal handler for setting default course mode expiration dates
"""
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler, modulestore

from course_modes.models import CourseMode, CourseModeExpirationConfig
from certificates import models as cert_models
from contentstore.views import certificates as store_certificates


from appsembleredx.app_settings import (
    DEFAULT_COURSE_MODE_SLUG, 
    mode_name_from_slug, 
    USE_OPEN_ENDED_CERTS_DEFAULTS,
    ALWAYS_ENABLE_SELF_GENERATED_CERTS
)


DEFAULT_CERT = '{"course_title": "", "name": "Default", "is_active": true, "signatories": [], "version": 1, "editing": false, "description": "Default certificate"}'


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

    if not USE_OPEN_ENDED_CERTS_DEFAULTS:
        return

    store = modulestore()
    course = store.get_course(course_key)
    if course.cert_defaults_set:
        return

    course.certificates_display_behavior = 'early_with_info'
    course.certificates_show_before_end = True  # deprecated anyhow
    course.cert_html_view_enabled = True
    course.cert_defaults_set = True
    course.issue_badges = False
    course.save()
    store.update_item(course, course._edited_by)


@receiver(SignalHandler.course_published)
def _enable_self_generated_certs_on_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    If feature is enabled, always enable self generated certs on published
    courses
    """
    if not ALWAYS_ENABLE_SELF_GENERATED_CERTS:
        return
    store = modulestore()
    course = store.get_course(course_key)
    enabled = cert_models.CertificateGenerationCourseSetting(course_key=course_key, enabled=True)
    enabled.save()


@receiver(SignalHandler.pre_publish)
def _make_default_active_certificate(sender, course_key, replace=False, **kwargs):  # pylint: disable=unused-argument
    """
    Create an active default certificate on the course
    """
    if not USE_OPEN_ENDED_CERTS_DEFAULTS:
        return

    store = modulestore()
    course = store.get_course(course_key)
    if course.active_default_cert_created:
        return        

    default_cert_data = DEFAULT_CERT
    new_cert = store_certificates.CertificateManager.deserialize_certificate(course, DEFAULT_CERT)
    if replace:
        course.certificates['certificates'] = [new_cert.certificate_data,]
    else:
        course.certificates['certificates'].append(new_cert.certificate_data)
    course.active_default_cert_created = True 
    course.save()
    store.update_item(course, course._edited_by)

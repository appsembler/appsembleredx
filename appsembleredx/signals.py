import copy
from functools import partial
import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler, modulestore
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from opaque_keys.edx.keys import CourseKey

try:
    from cache_toolbox.core import del_cached_content
except ImportError:  # moved after eucalyptus.2
    try:
        from openedx.core.djangoapps.contentserver.caching import del_cached_content
    except ImportError:
        from contentserver.caching import del_cached_content

from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent
from django.core.files.storage import get_storage_class

from course_modes.models import CourseMode
from certificates import models as cert_models

from appsembleredx.app_settings import (
    DEFAULT_COURSE_MODE_SLUG,
    mode_name_from_slug,
    USE_OPEN_ENDED_CERTS_DEFAULTS,
    ALWAYS_ENABLE_SELF_GENERATED_CERTS,
    DISABLE_SELF_GENERATED_CERTS_FOR_SELF_PACED,
    DEFAULT_CERT_SIGNATORIES,
    ACTIVATE_DEFAULT_CERTS,
    DISABLE_COURSE_COMPLETION_BADGES
)

DEFAULT_CERT = """
    {{"course_title": "", "name": "Default", "is_active": {},
    "signatories": {}, "version": 1, "editing": false,
    "description": "Default certificate"}}
"""


def make_default_cert(course_key):
    """
    Add any signatories to default cert string and return the string
    """

    default_cert = DEFAULT_CERT

    if DEFAULT_CERT_SIGNATORIES:
        signatories = DEFAULT_CERT_SIGNATORIES
        updated = []
        for i, sig in enumerate(signatories):
            default_cert_signatory = copy.deepcopy(sig)
            default_cert_signatory['id'] = i
            theme_asset_path = sig['signature_image_path']
            sig_img_path = store_theme_signature_img_as_asset(course_key, theme_asset_path)
            default_cert_signatory['signature_image_path'] = sig_img_path
            updated.append(default_cert_signatory)
        default_cert_signatories = json.dumps(updated)
        return default_cert.format(str(ACTIVATE_DEFAULT_CERTS).lower(), default_cert_signatories)

    else:
        return default_cert.format(str(ACTIVATE_DEFAULT_CERTS).lower(), "[]")


def store_theme_signature_img_as_asset(course_key, theme_asset_path):
    """
    to be able to edit or delete signatories and Certificates properly
    we must store signature PNG file as course content asset.
    Store file from theme as asset.
    Return static asset URL path
    """
    filename = theme_asset_path.split('/')[-1]
    static_storage = get_storage_class(settings.STATICFILES_STORAGE)()
    path = static_storage.path(theme_asset_path)

    content_loc = StaticContent.compute_location(course_key, theme_asset_path)
    # TODO: exception if not png
    sc_partial = partial(StaticContent, content_loc, filename, 'image/png')
    with open(path, 'rb') as imgfile:
        content = sc_partial(imgfile.read())

    # then commit the content
    contentstore().save(content)
    del_cached_content(content.location)

    # return a path to the asset.  new style courses will need extra /
    path_extra = "/" if course_key.to_deprecated_string().startswith("course") else ""
    return "{}{}".format(path_extra, content.location.to_deprecated_string())


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
    use_badges = settings.FEATURES.get('ENABLE_OPENBADGES', False)
    if not use_badges or DISABLE_COURSE_COMPLETION_BADGES:
        course.issue_badges = False
    course.save()
    try:
        store.update_item(course, course._edited_by)
    except AttributeError:
        store.update_item(course, 0)


@receiver(SignalHandler.course_published)
def enable_self_generated_certs(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    If not already enabled, enable self-generated certificates on course if:
    course is a self-paced course and self-generated certs on self-paced not explicitly disabled
    course is not self-paced and self-generated certs are explicitly enabled
    """
    course_key = unicode(course_key)
    course_key = CourseKey.from_string(course_key)
    course = CourseOverview.get_from_id(course_key)
    is_enabled_for_course = cert_models.CertificateGenerationCourseSetting.is_enabled_for_course(course_key)
    if is_enabled_for_course:
        return

    if course.self_paced and DISABLE_SELF_GENERATED_CERTS_FOR_SELF_PACED:
        return

    if not course.self_paced and not ALWAYS_ENABLE_SELF_GENERATED_CERTS:
        return
    cert_models.CertificateGenerationCourseSetting.set_enabled_for_course(course_key, True)


@receiver(SignalHandler.pre_publish)
def _make_default_active_certificate(sender, course_key, replace=False,
                                     force=False, **kwargs):  # pylint: disable=unused-argument
    """
    Create an active default certificate on the course.  If we pass replace=True, it will
    overwrite existing active certs.  If we pass force=True (the management command always
    does), then it won't care if we are using open ended cert defaults.  We do the latter
    since a customer might wish not to enable student-generated certs but still have a
    default certificate ready, for example, if they want instructors to generate the HTML
    certs.
    """
    if not USE_OPEN_ENDED_CERTS_DEFAULTS and not force:
        return

    store = modulestore()
    course = store.get_course(course_key)
    if course.active_default_cert_created and not replace:
        return

    default_cert_data = make_default_cert(course_key)

    from contentstore.views import certificates as store_certificates
    new_cert = store_certificates.CertificateManager.deserialize_certificate(course, default_cert_data)
    if 'certificates' not in course.certificates:
        course.certificates['certificates'] = []
    if replace:
        course.certificates['certificates'] = [new_cert.certificate_data, ]
    else:
        course.certificates['certificates'].append(new_cert.certificate_data)
    course.active_default_cert_created = True
    course.save()
    try:
        store.update_item(course, course._edited_by)
    except AttributeError:
        store.update_item(course, 0)

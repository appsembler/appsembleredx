""" Unit tests for signal handlers on course publication activity
"""
from functools import wraps
import json
import mock

from django.core.exceptions import ObjectDoesNotExist

try:  # LMS
    from certificates.models import (
        CertificateGenerationConfiguration, CertificateGenerationCourseSetting)
except ImportError:  # CMS
    from lms.djangoapps.certificates.models import (
        CertificateGenerationConfiguration, CertificateGenerationCourseSetting)
from course_modes.models import CourseMode
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from appsembleredx import signals


def certs_feature_enabled(func):
    @wraps(func)
    @mock.patch.dict('appsembleredx.signals.settings.FEATURES', {'CERTIFICATES_ENABLED': True})
    def with_certs_enabled(*args, **kwargs):
        # reload to re-evaluate the decorated methods with new setting
        reload(signals)
        return func(*args, **kwargs)

    return with_certs_enabled


class BaseCertSignalsTestCase(ModuleStoreTestCase):

    def setUp(self):
        super(BaseCertSignalsTestCase, self).setUp()
        # allow self-paced courses
        SelfPacedConfiguration(enabled=True).save()
        self.course = CourseFactory.create(self_paced=True)
        self.store = modulestore()
        self.mock_app_settings = mock.Mock()


class LMSCertSignalsTestCase(BaseCertSignalsTestCase):

    def setUp(self):
        super(LMSCertSignalsTestCase, self).setUp()
        # Enable certificates generation config in db, overall
        CertificateGenerationConfiguration.objects.create(enabled=True)


class CertsSettingsSignalsTest(LMSCertSignalsTestCase):
    """ Tests for signal handlers changing cert and badge related settings on course
        publish or pre-publish.  Some of the handlers should not do anything 
        if certificates feature is not enabled.
    """

    @mock.patch.dict('appsembleredx.signals.settings.FEATURES', {'CERTIFICATES_ENABLED': False})
    def test_signal_handlers_disabler_decorator(self):
        """ Verify decorator works to return a noop function if CERTIFICATES_ENABLED is False
        """
        mock_decorated = mock.Mock()
        mock_decorated.__name__ = 'mocked'  # needed for functools.wrap
        ret_func = signals.disable_if_certs_feature_off(mock_decorated)
        self.assertNotEqual(ret_func, mock_decorated)
        self.assertTrue('noop_handler' in ret_func.__name__)

    @certs_feature_enabled
    def test_default_course_mode_changed_on_publish(self):
        """ Verify the signal handler sets new default course mode
        """
        # there should be no coursemode object for the course
        self.assertRaises(ObjectDoesNotExist, CourseMode.objects.get, **{"course_id": self.course.id})
        # publish signal creates a new coursemode object
        signals._default_mode_on_course_publish('store', self.course.id)
        newmode = CourseMode.objects.get(course_id=self.course.id)
        self.assertEqual(newmode.mode_slug, 'honor' )
        # second publish doesn't create a new coursemode object
        signals._default_mode_on_course_publish('store', self.course.id)
        modes = CourseMode.objects.filter(course_id=self.course.id)
        self.assertEqual(len(modes), 1)
    
    @certs_feature_enabled
    def test_cert_related_advanced_settings_as_expected_by_default(self):
        """ Verify that cert-related advanced course settings are what
            we think by default
        """
        self.assertEqual(self.course.certificates_display_behavior, 'end')
        self.assertFalse(self.course.certificates_show_before_end)
        self.assertFalse(self.course.cert_html_view_enabled)

    @certs_feature_enabled
    def test_cert_related_advanced_settings_features(self):
        """ Verify changes to cert-related advanced settings if we 
            enable the feature or don't enable it
        """
        signals._change_cert_defaults_on_pre_publish('store', self.course.id)
        course = self.store.get_course(self.course.id)
        self.assertEqual(course.certificates_display_behavior, 'end')
        self.assertFalse(course.certificates_show_before_end)
        self.assertFalse(course.cert_html_view_enabled)

        self.mock_app_settings.USE_OPEN_ENDED_CERTS_DEFAULTS = True
        with mock.patch('appsembleredx.signals.app_settings', new=self.mock_app_settings):
            signals._change_cert_defaults_on_pre_publish('store', self.course.id)
            course = self.store.get_course(self.course.id)
            self.assertEqual(course.certificates_display_behavior, 'early_with_info')
            self.assertTrue(course.certificates_show_before_end)
            self.assertTrue(course.cert_html_view_enabled)

    def test_badges_remain_disabled_after_pre_publish_with_feature_off(self):
        """ Verify that badges-related advanced course settings are not changed
            when we use related feature settings
        """        
        with mock.patch.dict('appsembleredx.signals.settings.FEATURES', {'ENABLE_OPENBADGES': False}):
            signals._change_badges_setting_on_pre_publish('store', self.course.id)
            course = self.store.get_course(self.course.id)
            self.assertFalse(course.issue_badges)

    def test_badges_remain_disabled_after_pre_publish_with_feature_on_but_course_completion_badges_off(self):
        """ Make sure we can enable to open badges feature overall but keep course completion
            badges off using our setting
        """    
        self.mock_app_settings.DISABLE_COURSE_COMPLETION_BADGES = True    
        with mock.patch.dict('appsembleredx.signals.settings.FEATURES', {'ENABLE_OPENBADGES': True}):
            with mock.patch('appsembleredx.signals.app_settings', new=self.mock_app_settings):
                signals._change_badges_setting_on_pre_publish('store', self.course.id)
                course = self.store.get_course(self.course.id)
                self.assertFalse(course.issue_badges)

    @certs_feature_enabled
    def test_enable_self_generated_certs_on_publish_for_self_paced(self):
        """ Verify that self-generated certs are not enabled for self-paced courses
            if it is explicitly disabled by setting
        """
        course = self.store.get_course(self.course.id)
        # this should fail when we move to Ginkgo
        self.assertFalse(CertificateGenerationCourseSetting.is_enabled_for_course(self.course.id))
        signals.enable_self_generated_certs('store', self.course.id)
        course = self.store.get_course(self.course.id)
        self.assertTrue(CertificateGenerationCourseSetting.is_enabled_for_course(course.id))

    @certs_feature_enabled
    def test_dont_enable_self_generated_certs_on_publish_for_self_paced_when_disabled_by_setting(self):
        """ Verify that self-generated certs are not enabled for self-paced courses
            if it is explicitly disabled by setting
        """
        self.mock_app_settings.DISABLE_SELF_GENERATED_CERTS_FOR_SELF_PACED = True    
        with mock.patch('appsembleredx.signals.app_settings', new=self.mock_app_settings):
            signals.enable_self_generated_certs('store', self.course.id)
            course = self.store.get_course(self.course.id)
            self.assertFalse(CertificateGenerationCourseSetting.is_enabled_for_course(course.id))

    @certs_feature_enabled
    def test_dont_enable_self_generated_certs_on_publish_for_instructor_paced(self):
        """ Verify that self-generated certs are not enabled for self-paced courses
            if it is explicitly disabled by setting
        """
        self.course = CourseFactory.create(self_paced=False)
        signals.enable_self_generated_certs('store', self.course.id)
        course = self.store.get_course(self.course.id)
        self.assertFalse(CertificateGenerationCourseSetting.is_enabled_for_course(course.id))

    @certs_feature_enabled
    def test_enable_self_generated_certs_on_publish_for_instructor_paced_if_always_enabled_by_setting(self):
        """ Verify that self-generated certs are not enabled for self-paced courses
            if it is explicitly disabled by setting
        """
        self.mock_app_settings.ALWAYS_ENABLE_SELF_GENERATED_CERTS = True    
        with mock.patch('appsembleredx.signals.app_settings', new=self.mock_app_settings):
            self.course = CourseFactory.create(self_paced=False)
            signals.enable_self_generated_certs('store', self.course.id)
            course = self.store.get_course(self.course.id)
            self.assertTrue(CertificateGenerationCourseSetting.is_enabled_for_course(course.id))


class CertsCreationSignalsTest(BaseCertSignalsTestCase):
    """ Tests for signal handlers which set up certificates.  None of the handlers should do anything 
        if certificates feature is not enabled.
    """

    def test_make_default_cert_string(self):
        """ Verify helper function that generates a string for default certificate creation
            that can be deserialized to a dictionary with proper values
        """
        self.mock_app_settings.DEFAULT_CERT_SIGNATORIES = {}
        self.mock_app_settings.ACTIVATE_DEFAULT_CERTS = True
        with mock.patch('appsembleredx.signals.app_settings', new=self.mock_app_settings):
            cert_string = signals.make_default_cert(self.course.id)
            to_dict = json.loads(cert_string)
            self.assertEqual(to_dict["course_title"], "")
            self.assertEqual(to_dict["name"], "Default")
            self.assertTrue(to_dict["is_active"])
            self.assertEqual(to_dict["signatories"], [])
            self.assertEqual(to_dict["version"], 1)
            self.assertFalse(to_dict["editing"])
            self.assertEqual(to_dict["description"], "Default certificate")

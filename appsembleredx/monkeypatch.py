from django.conf import settings

from xmodule import course_module
from course_modes import models as course_modes_models
from student.models import LinkedInAddToProfileConfiguration

from appsembleredx import app_settings
from appsembleredx import mixins

import logging
logger = logging.getLogger(__name__)

# some trickery here to get around AppRegsitryNotReady error b/c of translation strings otherwise
from django.utils import translation
orig_ugettext = translation.ugettext
translation.ugettext =  translation.ugettext_lazy


if 'cms' in settings.SETTINGS_MODULE:
	# if we are in CMS we need to mock out unimportable modules
	# load a fake certificates.views.support module for now
	class fakemodule(object):
		__path__ = []

	import sys
	logger.warn("Setting fake certificates.views.support module for CMS.  Not used in Studio")
	sys.modules['certificates.views.support'] = fakemodule()  # load an emtpty module

from certificates.views import webview
from certificates.signals import enable_self_generated_certs
from lms.djangoapps.certificates.signals import enable_self_generated_certs as enable_self_generated_certs_fullpath

# and then put back the originals
translation.ugettext = orig_ugettext


def get_CourseDescriptor_mixins():
	new_mixins = [mixins.XMLDefinitionChainingMixin, mixins.CertificatesExtensionMixin, ]
	if app_settings.ENABLE_CREDITS_EXTRA_FIELDS:
		new_mixins.append(mixins.CreditsMixin)
	if app_settings.ENABLE_INSTRUCTION_TYPE_EXTRA_FIELDS:
		new_mixins.append(mixins.InstructionTypeMixin)	
	return tuple(new_mixins)


logger.warn('Monkeypatching course_module.CourseDescriptor to add Appsembler Mixins')
orig_CourseDescriptor = course_module.CourseDescriptor
CDbases = course_module.CourseDescriptor.__bases__
course_module.CourseDescriptor.__bases__ = get_CourseDescriptor_mixins() + CDbases

logger.warn('Monkeypatching course_modes_models.CourseMode.DEFAULT_MODE_SLUG and ...DEFAULT_MODE')
orig_DEFAULT_MODE_SLUG = course_modes_models.CourseMode.DEFAULT_MODE_SLUG
course_modes_models.CourseMode.DEFAULT_MODE_SLUG = app_settings.DEFAULT_COURSE_MODE_SLUG
orig_DEFAULT_MODE = course_modes_models.CourseMode.DEFAULT_MODE
course_modes_models.CourseMode.DEFAULT_MODE = app_settings.DEFAULT_COURSE_MODE

logger.warn('Monkeypatching lms.djangoapps.certificates.views.webview._update_course_context to extend with Appsembler Mixin fields')
orig__update_course_context = webview._update_course_context
from appsembleredx import views
webview._update_course_context = views._update_course_context

# no 'honor code', just leave it blank.  Our clients probably won't have codes of honor
# and if they do they won't miss it. 
logger.warn('Monkeypatching LinkedIn add to profile honor code cert name')
orig_MODE_TO_CERT_NAME = LinkedInAddToProfileConfiguration.MODE_TO_CERT_NAME
del LinkedInAddToProfileConfiguration.MODE_TO_CERT_NAME['honor']


# override certificates handler which always enables self-gen'd certs for self-paced courses
# so that it only enables self-gen'd certs on self-paced if we set feature flag for it
# we have to disable celery tasks already registered for signal handlers in edx-platform
logger.warn('Monkeypatching lms.djangoapps.certificates.signals.enable_self_generated_certs to limit enabling of self-generated certs on self-paced courses by feature flag.')
orig_enable_self_generated_certs = enable_self_generated_certs
# task seems to be registered twice, as 'certificates.signals.enable_self_generated_certs', and
# 'lms.djangoapps.certificates.signals.enable_self_generated_certs'
enable_self_generated_certs.delay = lambda course_key:None
enable_self_generated_certs_fullpath.delay = lambda course_key:None

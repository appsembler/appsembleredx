from xmodule import course_module
from course_modes import models as course_modes_models
from xmodule.course_module import CourseFields

from appsembleredx import app_settings
from appsembleredx import mixins


def get_CourseDescriptor_mixins():
	new_mixins = [mixins.XMLDefinitionChainingMixin, mixins.CertificatesExtensionMixin, ]
	if app_settings.ENABLE_CREDITS_EXTRA_FIELDS:
		new_mixins.append(mixins.CreditsMixin)
	if app_settings.ENABLE_INSTRUCTION_TYPE_EXTRA_FIELDS:
		new_mixins.append(mixins.InstructionTypeMixin)	
	return tuple(new_mixins)


orig_CourseDescriptor = course_module.CourseDescriptor
CDbases = course_module.CourseDescriptor.__bases__
course_module.CourseDescriptor.__bases__ = get_CourseDescriptor_mixins() + CDbases


orig_DEFAULT_MODE_SLUG = course_modes_models.CourseMode.DEFAULT_MODE_SLUG
course_modes_models.CourseMode.DEFAULT_MODE_SLUG = app_settings.DEFAULT_COURSE_MODE_SLUG
orig_DEFAULT_MODE = course_modes_models.CourseMode.DEFAULT_MODE
course_modes_models.CourseMode.DEFAULT_MODE = app_settings.DEFAULT_COURSE_MODE


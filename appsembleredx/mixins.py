"""
Reusable mixins for XBlocks and/or XModules
"""

from django.conf import settings
from xblock.fields import Scope, String, Float, XBlockMixin

from . import app_settings

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


CREDITS_VIEW = 'credits_view'
INSTRUCTION_TYPE_VIEW = 'instruction_type_view'
CREDIT_PROVIDERS = app_settings.CREDIT_PROVIDERS
COURSE_INSTRUCTIONAL_METHODS = app_settings.COURSE_INSTRUCTIONAL_METHODS
COURSE_FIELDS_OF_STUDY = app_settings.COURSE_FIELDS_OF_STUDY
COURSE_INSTRUCTIONAL_METHOD_DEFAULT =  app_settings.COURSE_INSTRUCTIONAL_METHOD_DEFAULT
COURSE_INSTRUCTION_LOCATIONS =  app_settings.COURSE_INSTRUCTION_LOCATIONS

# this is included as a mixin in xmodule.course_module.CourseDescriptor


def build_field_values(values_dict):
    """
    pass a dict of values and return list for XBlock Field values property
    """
    return [{"value": key, "display_name": values_dict[key]['name']} for key in values_dict.keys()]


class XMLDefinitionChainingMixin(XBlockMixin):
    """
    Provide for chaining of definition_to_xml, definition_from_xml
    methods with any number of mixins.  This Mixin must be first in the chain
    for this to work
    """
    
    def definition_to_xml(self, resource_fs):
        # append any additional xml from Mixin Classes definition_to_xml methods
        # CourseModuleDescriptor and its superclass take resource_fs
        # as arg but return an xml object
        # TODO: this may not be right

        xmlobj = super(DefinitionsChainingMixin, self).definition_to_xml(resource_fs)

        super_bases = super(DefinitionsChainingMixin, self).__bases__

        for i in range(1, len(super_bases)):  # don't include this base
            klass = super_bases(i)
            try:
                xmlobj = klass.append_definition_to_xml(self, xmlobj)
            except AttributeError:
                pass
            
        return xmlobj

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        # update definition from Mixin Classes definition_from_xml methods
        # return definition, children
        # TODO: this may not be right

        definition, children = super(DefinitionsChainingMixin, cls).definition_from_xml(xml_object, system)
        super_bases = super(DefinitionsChainingMixin, cls).__bases__

        for i in range(1, len(super_bases)):  # don't include this base
            klass = super_bases(i)
            try:
                definition, children = klass.update_definition_from_xml(cls, definition, children)
            except AttributeError:
                pass
            
        return definition, children


class CreditsMixin(XBlockMixin):
    """
    Mixin that allows an author to specify a credit provider and a number of credit
    units.
    """
    credit_provider = String(
        display_name=_("Credit Provider"),
        help=_("Name of the entity providing the credit units"),
        values=build_field_values(CREDIT_PROVIDERS),
        scope=Scope.settings,
    )

    credits = Float(
        display_name=_("Credits"),
        help=_("Number of credits"),
        default=None,
        scope=Scope.settings,
    )

    credit_unit = String(
        display_name=_("Credit Unit"),
        help=_("Name of unit of credits; e.g., hours"),
        default=_("hours"),
        scope=Scope.settings,
    )


class InstructionTypeMixin(XBlockMixin):
    """ 
    Mixin that allows an author to specify attributes about the course's
    method, field of study, and location of instruction
    """
    field_of_study = String(display_name=_("Field of Study"),
        help=_("Topic/field classification of the course content"),
        values=build_field_values(COURSE_FIELDS_OF_STUDY),
        scope=Scope.content,
    )

    # we could create course_modes for this, but better to keep this separate.
    instructional_method = String(
        display_name=_("Instructional Method"),
        help=_("Type of instruction; e.g., classroom, self-paced"),
        default=COURSE_INSTRUCTIONAL_METHOD_DEFAULT,
        values=build_field_values(COURSE_INSTRUCTIONAL_METHODS),
        scope=Scope.settings,
    )

    instruction_location = String(        
        display_name=_("Instruction Location"),
        help=_("Physical location of insruction; for cases where Open edX courseware is used in a specific physical setting"),
        values=build_field_values(COURSE_INSTRUCTION_LOCATIONS),
        scope=Scope.settings,
    )


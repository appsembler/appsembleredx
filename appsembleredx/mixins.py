"""
Reusable mixins for XBlocks and/or XModules
"""
import inspect
from new import instancemethod

from xblock.fields import Scope, String, Float, Boolean, XBlockMixin
from xblock import internal
from xmodule import course_module, xml_module

from . import app_settings

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


CREDITS_VIEW = 'credits_view'
INSTRUCTION_TYPE_VIEW = 'instruction_type_view'
CREDIT_PROVIDERS = app_settings.CREDIT_PROVIDERS
CREDIT_PROVIDERS_DEFAULT = app_settings.CREDIT_PROVIDERS_DEFAULT
COURSE_INSTRUCTIONAL_METHODS = app_settings.COURSE_INSTRUCTIONAL_METHODS
COURSE_FIELDS_OF_STUDY = app_settings.COURSE_FIELDS_OF_STUDY
COURSE_INSTRUCTIONAL_METHOD_DEFAULT =  app_settings.COURSE_INSTRUCTIONAL_METHOD_DEFAULT
COURSE_INSTRUCTION_LOCATIONS =  app_settings.COURSE_INSTRUCTION_LOCATIONS
COURSE_INSTRUCTION_LOCATION_DEFAULT =  app_settings.COURSE_INSTRUCTION_LOCATION_DEFAULT

# this is included as a mixin in xmodule.course_module.CourseDescriptor


def build_field_values(values):
    """
    pass values and return list for XBlock Field values property
    can handle Dicts, sequences, and None values
    """
    if type(values).__name__ == 'dict':
        return [{"value": key, "display_name": values[key]['name']} for key in values.keys()]
    elif type(values).__name__ in ('tuple', 'list'):
        return [{"value": item, "display_name": item} for item in values]
    elif values == None:
        return None


class XMLDefinitionChainingMixin(XBlockMixin):
    """
    Provide for chaining of definition_to_xml, definition_from_xml
    methods with any number of mixins.  This Mixin must be first in the chain
    for this to work
    """

    # (Pdb) mro  (of self)
    # (<class 'xblock.internal.CourseDescriptorWithMixins'>, 
    # <class 'xmodule.course_module.CourseDescriptor'>, 
    # <class 'appsembleredx.mixins.XMLDefinitionChainingMixin'>, 
    # <class 'appsembleredx.mixins.CertificatesExtensionMixin'>, 
    # <class 'appsembleredx.mixins.CreditsMixin'>, 
    # <class 'appsembleredx.mixins.InstructionTypeMixin'>, 
    # <class 'xmodule.course_module.CourseFields'>, 
    # <class 'xmodule.seq_module.SequenceDescriptor'>, 
    # <class 'xmodule.seq_module.SequenceFields'>, 
    # <class 'xmodule.seq_module.ProctoringFields'>, 
    # <class 'xmodule.mako_module.MakoModuleDescriptor'>, 
    # <class 'xmodule.mako_module.MakoTemplateBlockBase'>, 
    # <class 'xmodule.xml_module.XmlDescriptor'>, 
    # <class 'xmodule.xml_module.XmlParserMixin'>, 
    # <class 'xmodule.x_module.XModuleDescriptor'>, 
    # <class 'xmodule.x_module.HTMLSnippet'>, 
    # <class 'xmodule.x_module.ResourceTemplates'>, 
    # <class 'lms.djangoapps.lms_xblock.mixin.LmsBlockMixin'>, 
    # <class 'xmodule.modulestore.inheritance.InheritanceMixin'>, 
    # <class 'xmodule.x_module.XModuleMixin'>, 
    # <class 'xmodule.x_module.XModuleFields'>, 
    # <class 'xblock.core.XBlock'>, 
    # <class 'xblock.mixins.XmlSerializationMixin'>, 
    # <class 'xblock.mixins.HierarchyMixin'>, 
    # <class 'xmodule.mixin.LicenseMixin'>, 
    # <class 'xmodule.modulestore.edit_info.EditInfoMixin'>, 
    # <class 'cms.lib.xblock.authoring_mixin.AuthoringMixin'>, 
    # <class 'xblock.XBlockMixin'>, 
    # <class 'xblock.core.XBlockMixin'>, 
    # <class 'xblock.mixins.ScopedStorageMixin'>, 
    # <class 'xblock.mixins.RuntimeServicesMixin'>, 
    # <class 'xblock.mixins.HandlersMixin'>, 
    # <class 'xblock.mixins.IndexInfoMixin'>, 
    # <class 'xblock.mixins.ViewsMixin'>, 
    # <class 'xblock.core.SharedBlockBase'>, 
    # <class 'xblock.plugin.Plugin'>, 
    # <type 'object'>)

    
    def definition_to_xml(self, resource_fs):
        """
        append any additional xml from Mixin Classes definition_to_xml methods
        """
        
        # needs to call definition_to_xml on SequenceDescriptor class first
        # and then append XML from there.  CourseDescriptor's definiton_to_xml calls
        # super() which runs SequenceDescriptor's, then adds, textbooks xml, then
        # explicitly calls LicenseMixin's add_license_to_xml()

        xmlobj = resource_fs  # not really an XML object but first called needs this val.
        mro = list(inspect.getmro(type(self)))
        mro.reverse()
        dont_call_twice = (str(self.__class__), 
                           "<class 'xblock.internal.CourseDescriptorWithMixins'>",  # generated class name
                           str(course_module.CourseDescriptor), 
                           str(XMLDefinitionChainingMixin),
                           str(xml_module.XmlParserMixin)
                           )

        for klass in mro:
            if str(klass) in dont_call_twice: 
                continue

            if type(getattr(klass, 'definition_to_xml', None)) == instancemethod:
                try:
                    xmlobj = klass.definition_to_xml(self, xmlobj)
                except NotImplementedError:  # some base classes raise this
                    continue

        return xmlobj

    # @classmethod
    # def definition_from_xml(cls, xml_object, system):
    #     # update definition from Mixin Classes definition_from_xml methods
    #     # return definition, children
    #     # TODO: this may not be right

    #     definition, children = super(XMLDefinitionChainingMixin, cls).definition_from_xml(xml_object, system)
    #     super_bases = super(XMLDefinitionChainingMixin, cls).__bases__

    #     for i in range(1, len(super_bases)):  # don't include this base
    #         klass = super_bases(i)
    #         try:
    #             definition, children = klass.update_definition_from_xml(cls, definition, children)
    #         except AttributeError:
    #             pass
            
    #     return definition, children


class CertificatesExtensionMixin(XBlockMixin):
    """
    Mixin to store custom fields about certificates
    """
    # store whether we have set defaults for cert-related adv. settings
    cert_defaults_set = Boolean(
        default=False,
        scope=Scope.content)
    # store whether we have created a default active cert
    active_default_cert_created = Boolean(
        default=False,
        scope=Scope.content)

    def definition_to_xml(self, xml_object):
        print "in CertificatesExtensionMixin definition_to_xml"
        for field in ('cert_defaults_set', 'active_default_cert_created'):
            if getattr(self, field, None):
                xml_object.set(field, str(getattr(self, field)))
        return xml_object

class CreditsMixin(XBlockMixin):
    """
    Mixin that allows an author to specify a credit provider and a number of credit
    units.
    """
    credit_provider = String(
        display_name=_("Credit Provider"),
        help=_("Name of the entity providing the credit units"),
        values=build_field_values(CREDIT_PROVIDERS),
        default=CREDIT_PROVIDERS_DEFAULT,
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

    def definition_to_xml(self, xml_object):
        print "in CreditsMixin definition_to_xml"
        for field in ('credit_provider', 'credits', 'credit_unit'):
            if getattr(self, field, None):
                xml_object.set(field, str(getattr(self, field)))
        return xml_object


class InstructionTypeMixin(XBlockMixin):
    """ 
    Mixin that allows an author to specify attributes about the course's
    method, field of study, and location of instruction
    """
    field_of_study = String(display_name=_("Field of Study"),
        help=_("Topic/field classification of the course content"),
        values=build_field_values(COURSE_FIELDS_OF_STUDY),
        scope=Scope.settings,
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
        default=COURSE_INSTRUCTION_LOCATION_DEFAULT,
        scope=Scope.settings,
    )

    def definition_to_xml(self, xml_object):
        print "in InstructionTypeMixin definition_to_xml"
        for field in ('field_of_study', 'instructional_method', 'instruction_location'):
            if getattr(self, field, None):
                xml_object.set(field, str(getattr(self, field)))
        return xml_object

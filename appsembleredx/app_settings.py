from os import environ

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from course_modes import models as course_modes_models

try:
    ENV_TOKENS = settings.ENV_TOKENS['APPSEMBLER_FEATURES']

    # courses
    DEFAULT_COURSE_MODE_SLUG = ENV_TOKENS.get("DEFAULT_COURSE_MODE_SLUG", "honor")
    mode_name_from_slug = _(DEFAULT_COURSE_MODE_SLUG.capitalize())
    try:
        DEFAULT_COURSE_MODE = course_modes_models.Mode(DEFAULT_COURSE_MODE_SLUG, mode_name_from_slug, 0, '', 'usd', None, None, None)
    except TypeError:
        # eucalyptus adds new field, bulk_sku
        DEFAULT_COURSE_MODE = course_modes_models.Mode(DEFAULT_COURSE_MODE_SLUG, mode_name_from_slug, 0, '', 'usd', None, None, None, None)
    
    ENABLE_CREDITS_EXTRA_FIELDS = ENV_TOKENS.get("ENABLE_CREDITS_EXTRA_FIELDS", False)
    CREDIT_PROVIDERS = ENV_TOKENS.get("CREDIT_PROVIDERS", [])
    CREDIT_PROVIDERS_DEFAULT = ENV_TOKENS.get("CREDIT_PROVIDERS_DEFAULT", None)
    DEFAULT_ACCREDITATION_HELP = _("Additional or alternative explanation of accreditation conferred, standards met, or similar description.")
    ACCREDITATION_CONFERRED_HELP = ENV_TOKENS.get("ACCREDITATION_CONFERRED_HELP", DEFAULT_ACCREDITATION_HELP)
    
    ENABLE_INSTRUCTION_TYPE_EXTRA_FIELDS = ENV_TOKENS.get("ENABLE_INSTRUCTION_TYPE_EXTRA_FIELDS", [])
    COURSE_INSTRUCTIONAL_METHODS = ENV_TOKENS.get("COURSE_INSTRUCTIONAL_METHODS", [])
    COURSE_FIELDS_OF_STUDY = ENV_TOKENS.get("COURSE_FIELDS_OF_STUDY", [])
    COURSE_INSTRUCTIONAL_METHOD_DEFAULT = ENV_TOKENS.get("COURSE_INSTRUCTIONAL_METHOD_DEFAULT", None)
    COURSE_INSTRUCTION_LOCATIONS = ENV_TOKENS.get("COURSE_INSTRUCTION_LOCATIONS", [])
    COURSE_INSTRUCTION_LOCATION_DEFAULT = ENV_TOKENS.get("COURSE_INSTRUCTION_LOCATION_DEFAULT", None)

    # certificates
    USE_OPEN_ENDED_CERTS_DEFAULTS = ENV_TOKENS.get("USE_OPEN_ENDED_CERTS_DEFAULTS", False)
    ACTIVATE_DEFAULT_CERTS = ENV_TOKENS.get("ACTIVATE_DEFAULT_CERTS", True)
    ALWAYS_ENABLE_SELF_GENERATED_CERTS = ENV_TOKENS.get("ALWAYS_ENABLE_SELF_GENERATED_CERTS", False)
    CERTS_HTML_VIEW_CONFIGURATION = ENV_TOKENS.get("CERTS_HTML_VIEW_CONFIGURATION", None)
    LINKEDIN_ADDTOPROFILE_COMPANY_ID = ENV_TOKENS.get("LINKEDIN_ADDTOPROFILE_COMPANY_ID", None)
    LINKEDIN_ADDTOPROFILE_LICENSE_ID = ENV_TOKENS.get("LINKEDIN_ADDTOPROFILE_LICENSE_ID", None)
    DEFAULT_CERT_SIGNATORIES = ENV_TOKENS.get("DEFAULT_CERT_SIGNATORIES", None)

    # badges
    DISABLE_COURSE_COMPLETION_BADGES = ENV_TOKENS.get("DISABLE_COURSE_COMPLETION_BADGES", False)


except AttributeError, e:
    # these won"t be available in test
    if environ.get("DJANGO_SETTINGS_MODULE") in (
            "lms.envs.acceptance", "lms.envs.test",
            "cms.envs.acceptance", "cms.envs.test"):
        pass
    else:
        raise

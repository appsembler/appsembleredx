from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from course_modes import models as course_modes_models

try:
    ENV_TOKENS = settings.ENV_TOKENS  

    # courses
    DEFAULT_COURSE_MODE_SLUG = ENV_TOKENS.get("APPSEMBLER_DEFAULT_COURSE_MODE_SLUG", "HONOR")
    mode_name_from_slug = _(DEFAULT_COURSE_MODE_SLUG.capitalize())
    DEFAULT_COURSE_MODE = course_modes_models.Mode(DEFAULT_COURSE_MODE_SLUG, mode_name_from_slug, 0, '', 'usd', None, None, None)
    
    USE_OPEN_ENDED_CERTS_DEFAULTS = ENV_TOKENS.get("APPSEMBLER_USE_OPEN_ENDED_CERTS_DEFAULTS", False)
    ENABLE_CREDITS_EXTRA_FIELDS = ENV_TOKENS.get("APPSEMBLER_ENABLE_CREDITS_EXTRA_FIELDS", False)
    CREDIT_PROVIDERS = ENV_TOKENS.get("APPSEMBLER_CREDIT_PROVIDERS", {})
    
    ENABLE_INSTRUCTION_TYPE_EXTRA_FIELDS = ENV_TOKENS.get("APPSEMBLER_ENABLE_INSTRUCTION_TYPE_EXTRA_FIELDS", [])
    COURSE_INSTRUCTIONAL_METHODS = ENV_TOKENS.get("APPSEMBLER_COURSE_INSTRUCTIONAL_METHODS", {})
    COURSE_INSTRUCTION_LOCATIONS = ENV_TOKENS.get("APPSEMBLER_COURSE_INSTRUCTION_LOCATIONS", {})
    COURSE_FIELDS_OF_STUDY = ENV_TOKENS.get("APPSEMBLER_COURSE_FIELDS_OF_STUDY", {})
    COURSE_INSTRUCTIONAL_METHOD_DEFAULT = ENV_TOKENS.get("APPSEMBLER_COURSE_INSTRUCTIONAL_METHOD_DEFAULT", None)

    # certificates


except AttributeError:
    # these won"t be available in test
    if environ.get("DJANGO_SETTINGS_MODULE") in (
            "lms.envs.acceptance", "lms.envs.test",
            "cms.envs.acceptance", "cms.envs.test"):
        pass
    else:
        raise

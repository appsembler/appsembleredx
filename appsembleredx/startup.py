"""
Django initialization.
"""
from edxmako import add_lookup
from appsembleredx import signals

def run():
    """
    Add our templates to the Django site.
    """
    # Add our mako templates
    add_lookup('main', 'templates', __name__)      # For LMS
    add_lookup('lms.main', 'templates', __name__)  # For CMS
	
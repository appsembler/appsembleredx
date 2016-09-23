import logging

from django.contrib.auth.decorators import login_required

from edxmako.shortcuts import render_to_response
from xblock import fields

from appsembleredx.monkeypatch import (
	orig__update_course_context,
	get_CourseDescriptor_mixins
)


log = logging.getLogger(__name__)

@login_required
def index(request):
    context = {}
    return render_to_response('boilerplate/index.html', context)


# CERTIFICATES-RELATED
def _update_course_context(request, context, course, platform_name):
	"""
	Course-related context for certificate webview, extended
	with Mixin fields
	"""

	orig__update_course_context(request, context, course, platform_name)

	# add our course extension fields
	course_mixins = get_CourseDescriptor_mixins()
	for mixin in course_mixins:
		for f in mixin.fields:
			context[f] = getattr(course, f)

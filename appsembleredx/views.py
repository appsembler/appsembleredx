import logging

from django.contrib.auth.decorators import login_required

from edxmako.shortcuts import render_to_response
from xblock import fields


log = logging.getLogger(__name__)

@login_required
def index(request):
    context = {}
    return render_to_response('boilerplate/index.html', context)

# -*- coding: utf-8 -*-
import json

from django.db import migrations

from appsembleredx import app_settings


def get_models(apps):
    CourseMode = apps.get_model("course_modes", "CourseMode")
    return (CourseMode,)


def fix_honor_course_mode_slugs(apps, schema_editor):
    """ switch any audit course modes to our default mode slug
    """
    (CourseMode, ) = get_models(apps)

    for cm in CourseMode.objects.all():
        if cm.mode_slug == 'HONOR':
            cm.mode_slug = 'honor'
            cm.mode_display_name = 'Honor'
            cm.save()


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0001_initial'),
        ('appsembleredx', '0001_data_set_default_course_mode'),
    ]

    operations = [
        migrations.RunPython(fix_honor_course_mode_slugs),
    ]
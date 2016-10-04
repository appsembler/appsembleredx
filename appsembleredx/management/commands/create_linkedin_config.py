# run this to enable LinkedIn configuration on an Open edX install
# called by Ansible playbook

from django.core.management.base import BaseCommand, CommandError

from student import models

from appsembleredx import app_settings


class Command(BaseCommand):
    help = """Creates a LinkedInAddToProfileConfiguration record to enable 
    certificate sharing on LinkedIn   
    """

    def handle(self, *args, **options):
        
        def stdout(msg, style=self.style.NOTICE):
            self.stdout.write(style(msg))
        
        company_id = app_settings.LINKEDIN_ADDTOPROFILE_COMPANY_ID
        # license_id is an optional custom field that may not exist in the profile
        # introduced in edx-platform appsembler/feature/add-to-linkedin-with-license-id
        license_id = app_settings.LINKEDIN_ADDTOPROFILE_LICENSE_ID

        if not company_id:
        	raise CommandError("You must specify a value for APPSEMBLER_FEATURES['LINKEDIN_ADDTOPROFILE_COMPANY_ID'] in your env.json file")

        try:
            enable =  models.LinkedInAddToProfileConfiguration(company_identifier=company_id, license_id=license_id or "", enabled=True)
            enable.save()
        except:  # pylint: disable=broad-except
            stdout("Couldn't enable a LinkedIn Add to Profile configuration", style=self.style.ERROR)
            raise CommandError("Couldn't enable a LinkedIn Add to Profile configuration")
        
        stdout('Enabled a LinkedIn Add to Profile configuration')
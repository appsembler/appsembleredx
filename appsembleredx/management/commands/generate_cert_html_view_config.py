# this will generate an HTML View Configuration for certs based
# on ENV token values

import json

from django.core.management.base import BaseCommand, CommandError

from certificates import models

from appsembleredx import app_settings


class Command(BaseCommand):
    help = """Creates a CertificateHtmlViewConfiguration from
    dict in settings.
    """

    def handle(self, *args, **options):

        def stdout(msg, style=self.style.NOTICE):
            self.stdout.write(style(msg))

        try:
            config = app_settings.CERTS_HTML_VIEW_CONFIGURATION
            if not config:
                raise CommandError("Nothing to generate.  Set APPSEMBLER_CERTS_HTML_VIEW_CONFIGURATION "
                                   "in your lms/cms.env.json")

            # disable all old configs
            try:
                existing_configs = models.CertificateHtmlViewConfiguration.objects.all()
                for old in existing_configs:
                    old.enabled = False
                    old.save()
                stdout('Disabled old HTML View Configurations for certs')
            except models.CertificateHtmlViewConfiguration.DoesNotExist:
                pass
            htmlviewconfig = models.CertificateHtmlViewConfiguration(configuration=json.dumps(config), enabled=True)
            htmlviewconfig.save()
        except Exception:  # pylint: disable=broad-except
            stdout("Couldn't set an HTML View Configuration for certs", style=self.style.ERROR)
            raise CommandError("Couldn't set an HTML View Configuration for certs")

        stdout('Set an HTML View Configuration for certs')

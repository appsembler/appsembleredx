# run this to enable self-generated certs on an Open edX install
# called by Ansible playbook

from django.core.management.base import BaseCommand, CommandError

from certificates import models


class Command(BaseCommand):
    help = """Creates a CertificateGenerationConfiguration record to enable
    self-generated certificates.
    """

    def handle(self, *args, **options):

        def stdout(msg, style=self.style.NOTICE):
            self.stdout.write(style(msg))

        try:
            enable = models.CertificateGenerationConfiguration(enabled=True)
            enable.save()
        except Exception:  # pylint: disable=broad-except
            stdout("Couldn't enable self-generated certs", style=self.style.ERROR)
            raise CommandError("Couldn't enable self-generated certs")

        stdout('Enabled self-generated certificates')

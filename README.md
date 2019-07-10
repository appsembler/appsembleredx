# appsembleredx

A poorly named common package with extensions and modifications for Open edX course certificates.
It is deprecated past the Ficus Open edX release but known to work on Dogwood, Eucalyptus, and Ficus releases.  
Its successor is <https://github.com/appsembler/appsembler_credentials_extensions>.

Course certificates and possibly badges will eventually move to the `credentials` package, so this package may need to be reworked to run in that service, or in both services.  

(Built on Appsembler edx boilerplate by Filip Jukic.)

## HTML certificate setup

The `appsembleredx` package provides a means to perform common setup to tailor HTML certificates to the way we want to use them with our clients.  

The `appsembleredx` package contains several monkeypatches adding signal handlers to the course/courseware publication events.  Any new course, provided the relevant feature flags are included in `EDXAPP_APPSEMBER_FEATURES` (see below) will be set up with an activated HTML certificate for 'honor' code students, which will have the signatories included in the configuration (also see below).  

### Configuration via Ansible

In `server-vars.yml`:
* Add to `edxapp_extra_requirements`:
    - `- name: 'git+https://github.com/appsembler/appsembleredx@master#egg=appsembleredx'`
* Add to `ADDL_INSTALLED_APPS`
    - `- appsemblerdx`
* Add to `EDXAPP_APPSEMBLER_FEATURES`:
    - If the customer needs HTML certs, will typically want to set the following basics, which are used as feature flags and configuration options by `appsembleredx`.  The following will set the default course mode (since Dogwood, default from edx-platform is `audit` which does not confer a certificate; allow certificates to be generated before a specific close date; allow HTML view of certs; and allow self-generated certs.

```yaml
  DEFAULT_COURSE_MODE_SLUG: 'honor'
  USE_OPEN_ENDED_CERTS_DEFAULTS: true
  ALWAYS_ENABLE_SELF_GENERATED_CERTS: true
  CERTS_HTML_VIEW_CONFIGURATION:
    default:
      accomplishment_class_append: "accomplishment-certificate"
      platform_name: "{{ EDXAPP_PLATFORM_NAME }}"
      url: "{{EDXAPP_LMS_BASE_SCHEME}://{{EDXAPP_LMS_BASE}}"
      logo_src: "/static/themes/{{ edxapp_theme_name }}/images/branding/brand-logo.svg"
      logo_url: "{{EDXAPP_LMS_BASE_SCHEME}://{{EDXAPP_LMS_BASE}}"
      certificate_title: "Certificate of Completion"
    honor:
      certificate_type": "Honor" 
      certificate_title": "Certificate of Completion"
      document_body_class_append": "is-honorcode"
```

By default, if you set `USE_OPEN_ENDED_CERTS_DEFAULTS` to `true`, `appsembleredx` will activate all new certificates as well as create them.  Some customers (ASU Starbucks is one example) will not want them activated by default (in their case, certs are simply a required bridge for badges).  If you don't want to activate them, add `ACTIVATE_DEFAULT_CERTS: false` to `EDXAPP_APPSEMBLER_FEATURES`.  


TODO: verify this: (note, it turned out that this flag was not enough.  Using just `ACTIVATE_DEFAULT_CERTS: false` did keep them from activating, but due to the architecture of `edx-platform`, a useless button for "Request Certificate" would still appear on the student Progress page.  Until that's fixed, you cannot use `USE_OPEN_ENDED_CERTS_DEFAULTS` at all unless you want that button to appear on all courses.)

Not all customers use signatories.  If they do not, you will need to add here: `DEFAULT_CERT_SIGNATORIES:[]`; otherwise something like:

```yaml
  DEFAULT_CERT_SIGNATORIES:
    - name: "Dennis Calvin"
      title: "Director"
      organization: "Penn State Extension"
      signature_image_path: "themes/{{ edxapp_theme_name }}/images/cert-sig-dennis-calvin.jpg"
```

You will need to make sure your customer-specific comprehensive theme subdirectory has copies of cert signature image files under both `cms/static/images` and `lms/static/images`, since the CMS service variant is used to create the course certificates.

If the customer is using LinkedIn-certificate integration, also add similar information to `EDXAPP_APPSEMBLER_FEATURES`
```
LINKEDIN_ADDTOPROFILE_COMPANY_ID: 0_g6VnTfEs2C9maEwUDNA0hgeSWfTlTH8r9zCkw7mBYW7erPuKj__xxxxxxxxxxxx-m0L6A6mLjErM6PJiwMkk6nYZylU7__75hCVwJdOTZCAkdv
```
our customizations to the LinkedIn-cert integration also support sending a value for LinkedIn's License Id field, which you can use by adding to `EDXAPP_APPSEMBLER_FEATURES `:

```
LINKEDIN_ADDTOPROFILE_LICENSE_ID: NASBA 103413
```

### Commands to run on the server

Some steps must be run using Django management commands on the server; as it has reached end of life there are no longer plans to automate these in Ansible.  `appsembler_credentials_extensions` does not require running these manually as part of a normal deployment.  

To run manually on the server, as `edxapp` user
* `cd /edx/app/edxapp/edx-platform`
* `source ~/edxapp_env`
* `./manage.py cms migrate appsembleredx --settings=aws_appsembler`
* `./manage.py cms enable_self_generated_certs --settings=aws_appsembler`
* `./manage.py cms generate_cert_html_view_config --settings=aws_appsembler`
* `./manage.py cms appsembler_setup_courses --all --settings=aws_appsembler` - (this one is run last and will set up the default HTML cert for all pre-existing courses, or for a specific course if you use a course id instead of the `--all` argument.)

If the customer is using LinkedIn-certificate integration, also run
* `./manage.py cms created_linkedin_config --settings=aws_appsembler`

#### Troubleshooting

If you encounter an error running the management commands, it is probably because the process that generates the new default certs can't find the signature image files for the cert signatories. These files are included in the theme package and you may need first to make sure they are included in the static files dirs.  In this case you should manually run `./manage.py cms collectstatic --settings=aws_appsembler`, `./manage.py lms collectstatic --settings=aws_appsembler` and try again.

Another common problem spot is having more than one enabled certificate html view configuration, particularly Eucalyptus+ which for cert previews will just grab any html view configuration.  If you are getting `NameError`s or other Mako errors displaying the certificates, this is probably the problem. Try something like 

```bash
sudo su edxapp -s /bin/bash
./manage.py lms dbshell --settings=aws_appssembler
sql > delete from certificates_certificatehtmlviewconfiguration where id != (YOUR GOOD ID)
```

You may even need to manually create a new certificate html view configuration through the admin panel, copying and pasting the latest good value which will have been created via the management command.  I don't yet understand why, but old html view configuration seem to be getting cached.

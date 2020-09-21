from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
# from cohort.import_i2b2 import get_unique_patient_count_from_org_union

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cohort_back.settings')

app = Celery('cohort_back')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


#
# app.conf.beat_schedule = {
#     'add-every-30-seconds': {
#         'task': 'cohort_back.celery.import_i2b2',
#         'schedule': 5.0
#     },
# }
# app.conf.timezone = 'UTC'


def create_fake_arbo(user):
    from cohort.models import Perimeter
    from explorations.models import Exploration
    p1 = Perimeter()
    p1.name = "Équipe de soin"
    p1.description = "Les données des patients/visites qui sont passés par mes services."
    p1.data_type = "ORG"
    p1.fhir_query = "/PractitionerRole/id_aph=me"  # Fixme
    p1.access_nominative = True
    p1.access_pseudo_anonymised = False
    p1.owner = user
    p1.save()

    p2 = Perimeter()
    p2.name = "Protocole XYZ"
    p2.description = "Les données des patients/visites du protocole XYZ tel que demandé. "
    p2.data_type = "GROUP"
    p2.fhir_query = "/Group/user=me"  # Fixme
    p2.access_nominative = True
    p2.access_pseudo_anonymised = True
    p2.owner = user
    p2.save()

    p3 = Perimeter()
    p3.name = "Étude de faisabilité"
    p3.description = "Les patients/visites de toute l'AP-HP. "
    p3.data_type = "ORG"
    p3.fhir_query = "/Organization/all"  # Fixme
    p3.access_nominative = False
    p3.access_pseudo_anonymised = False
    p3.owner = user
    p3.save()

    p4 = Perimeter()
    p4.name = "Multi-centrique"
    p4.description = "Les données des patients/visites de toute l'AP-HP."
    p4.data_type = "ORG"
    p4.fhir_query = "/Organization/all"  # Fixme
    p4.access_nominative = False
    p4.access_pseudo_anonymised = True
    p4.owner = user
    p4.save()

    e = Exploration()
    e.name = "Exploration i2B2"
    e.description = "Import des cohortes générées dans i2b2."
    e.owner = user
    e.save()

    return p1, e


def create_cohort(user, perimeter, exploration, fhir_group, cohort_type):
    from explorations.models import Cohort, Request, RequestQuerySnapshot, RequestQueryResult
    name = fhir_group['name'][:50]
    fhir_id = fhir_group['fhir_id']
    create_date = fhir_group['creation_date']
    size = fhir_group['size']

    # If this cohort already exists, do not create it again
    if cohort_type == 'MY_PATIENTS':
        c = Cohort.objects.filter(owner=user, type='MY_PATIENTS').count()
        if c == 1:
            cohort = Cohort.objects.get(owner=user, type='MY_PATIENTS')
            cohort.fhir_groups_ids = fhir_id
            cohort.result_size = size
            cohort.save()
            return cohort
    elif cohort_type in ['IMPORT_I2B2', 'MY_ORGANIZATIONS']:
        cohort = Cohort.objects.filter(owner=user, name=name, fhir_groups_ids=str(int(fhir_id)), type=cohort_type)
        if cohort.count() == 1:
            return cohort[0]

    r = Request()
    r.owner = user
    r.name = name
    r.description = ""
    r.exploration = exploration
    r.data_type_of_query = "PATIENT"
    r.save()

    rqs = RequestQuerySnapshot()
    rqs.owner = user
    rqs.request = r
    rqs.serialized_query = "{}"
    rqs.save()

    rqr = RequestQueryResult()
    rqr.owner = user
    rqr.request_query_snapshot = rqs
    rqr.request = r
    rqr.request = r
    rqr.perimeter = perimeter
    rqr.result_size = size
    rqr.save()

    c = Cohort()
    c.owner = user
    c.name = name
    c.description = ""
    c.request_query_result = rqr
    c.request_query_snapshot = rqs
    c.request = r
    c.perimeter = perimeter
    c.fhir_groups_ids = fhir_id
    c.type = cohort_type
    c.result_size = size
    c.save()
    if create_date is not None:
        c.created_at = create_date
        c.save()
    return c


@app.task()
def import_i2b2():
    from cohort.models import User, Perimeter
    from cohort.import_i2b2 import get_user_cohorts, get_user_care_sites_cohorts
    from explorations.models import Cohort, Exploration

    for user in User.objects.all():
        if Perimeter.objects.filter(owner=user).count() < 1:
            p1, explo = create_fake_arbo(user)
        else:
            p1 = Perimeter.objects.get(owner=user, name="Équipe de soin")
            explo = Exploration.objects.get(owner=user, name="Exploration i2B2")

        cohorts = get_user_cohorts(user.username)
        for cohort in cohorts:
            create_cohort(user, p1, explo, cohort, 'IMPORT_I2B2')

        # Delete old i2b2 cohorts deleted in OMOP
        Cohort.objects \
            .filter(owner=user,  type='IMPORT_I2B2') \
            .exclude(fhir_groups_ids__in=[doc['fhir_id'] for doc in cohorts]).delete()

        care_sites = get_user_care_sites_cohorts(user.username)
        created_cohorts = []
        for care_site in care_sites:
            created_cohorts.append(create_cohort(user, p1, explo, care_site, 'MY_ORGANIZATIONS'))

        # Delete old organizations that do not exist anymore
        Cohort.objects \
            .filter(owner=user, type='MY_ORGANIZATIONS') \
            .exclude(uuid__in=[c.uuid for c in created_cohorts]).delete()

        if len(care_sites) > 0:
            # my_patients_size = get_unique_patient_count_from_org_union(
            #     org_ids=[cs['care_site_id'] for cs in care_sites])

            my_patients = {
                'fhir_id': ','.join([str(e['fhir_id']) for e in care_sites]),
                'name': "Mes patients",
                'size': -1,  # my_patients_size,
                'creation_date': None
            }

            # To add when count is correct
            # if my_patients['size'] > 0:
            create_cohort(user, p1, explo, my_patients, 'MY_PATIENTS')


@app.task()
def update_gitlab_issues():
    from voting.celery import update_with_gitlab_issues

    update_with_gitlab_issues()

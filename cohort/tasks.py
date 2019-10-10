import logging

from celery import shared_task, current_app

from datetime import datetime
from random import randint

from django.http import HttpResponse

from cohort.models import Perimeter
from cohort_back.settings import OMOP_COMPUTE_API_URL
from explorations.models import Exploration, Request, RequestQuerySnapshot, RequestQueryResult, Cohort
from requests import get, post

lorem_ipsum = "There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text. All the Lorem Ipsum generators on the Internet tend to repeat predefined chunks as necessary, making this the first true generator on the Internet. It uses a dictionary of over 200 Latin words, combined with a handful of model sentence structures, to generate Lorem Ipsum which looks reasonable. The generated Lorem Ipsum is therefore always free from repetition, injected humour, or non-characteristic words etc."
logger = logging.getLogger(__name__)


def import_cohorts_from_i2b2(user, jwt_access_token):
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
    logger.error("Type of jwt_access_token: {}".format(str(type(jwt_access_token))))
    chart_models = get(OMOP_COMPUTE_API_URL + "/chart_model/",
                       headers={"Authorization": "Bearer " + jwt_access_token}).json()['results']

    def create_cohort(fhir_group, cohort_type):
        # If this cohort already exists, do not create it again
        if cohort_type == 'MY_PATIENTS':
            c = Cohort.objects.filter(owner=user, type='MY_PATIENTS').count()
            if c == 1:
                Cohort.objects.get(owner=user, type='MY_PATIENTS').delete()
        elif cohort_type in ['IMPORT_I2B2', 'MY_ORGANIZATIONS']:
            c = Cohort.objects.filter(owner=user, name=fhir_group['name'],
                                      fhir_groups_ids=str(int(fhir_group['id']))).count()
            if c == 1:
                return
        r = Request()
        r.owner = user
        r.name = fhir_group['name']
        r.description = lorem_ipsum[
                        randint(0, int(len(lorem_ipsum) / 2)):randint(int(len(lorem_ipsum) / 2), len(lorem_ipsum))]
        r.exploration = e
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
        rqr.perimeter = p1
        rqr.result_size = fhir_group['quantity']
        rqr.save()

        c = Cohort()
        c.owner = user
        c.name = fhir_group['name']
        c.description = lorem_ipsum[
                        randint(0, int(len(lorem_ipsum) / 2)):randint(int(len(lorem_ipsum) / 2), len(lorem_ipsum))]
        c.request_query_result = rqr
        c.request_query_snapshot = rqs
        c.request = r
        c.perimeter = p1
        c.fhir_groups_ids = fhir_group['id']
        if 'extension' in fhir_group:
            c.created_at = datetime.strptime(fhir_group['extension'][0]['valueDate'], "%Y-%m-%d")
        c.type = cohort_type
        c.result_size = fhir_group['quantity']
        c.save()

        for chart_model in chart_models:
            respp = post(OMOP_COMPUTE_API_URL + "/chart_session/",
                         data={
                             "chart_model_id": chart_model['uuid'],
                             "cohorts_ids": c.fhir_groups_ids},
                         headers={"Authorization": "Bearer " + jwt_access_token})
            if respp.status_code != 201:
                logger.error('Error while sending a post request to the charting API, '
                             'response contains: {}'.format(str(respp.__dict__)))

    url = "https://fhir-r4-qual.eds.aphp.fr/Practitioner?_format=json&identifier={}".format(user.username)
    resp = get(url, headers={"Authorization": jwt_access_token})

    if resp.status_code != 200 or 'entry' not in resp.json() or len(resp.json()['entry']) != 1 \
            or str(resp.json()['entry'][0]['resource']['identifier'][0]['value']) != user.username:
        logger.error('Error while sending a get request to the FHIR API ({}), '
                     'response contains: {}'.format(url, str(resp.__dict__)))
        raise HttpResponse(status=500)

    id_fhir = resp.json()['entry'][0]['resource']['id']

    # Create I2B2 cohorts
    url = "https://fhir-r4-qual.eds.aphp.fr/Group?managing-entity={}".format(id_fhir)
    resp = get(url, headers={"Authorization": jwt_access_token})

    if resp.status_code == 200:
        data = resp.json()
        if 'entry' in data:
            logger.error("Got {} results for {}!".format(len(data['entry']), url))
            for fhir_group in data['entry']:
                create_cohort(fhir_group['resource'], cohort_type="IMPORT_I2B2")
    else:
        logger.error('Error while sending a get request to the FHIR API ({}), '
                     'response contains: {}'.format(url, str(resp.__dict__)))
        raise HttpResponse(status=500)

    # Create Org cohorts
    url = "https://fhir-r4-qual.eds.aphp.fr/PractitionerRole?practitioner={}".format(id_fhir)
    resp = get(url, headers={"Authorization": jwt_access_token})

    org_ids = []
    if resp.status_code == 200:
        data = resp.json()
        if 'entry' in data:
            logger.error("Got {} results for {}!".format(len(data['entry']), url))
            org_ids = [role['resource']['organization']['reference'].split('/')[1] for role in data['entry'] if
                       'organization' in role['resource']]
    else:
        logger.error('Error while sending a get request to the FHIR API ({}), '
                     'response contains: {}'.format(url, str(resp.__dict__)))
        raise HttpResponse(status=500)

    if len(org_ids) > 0:

        url = "https://fhir-r4-qual.eds.aphp.fr/Group?managing-entity=Organization/{}".format(','.join(org_ids))
        resp = get(url, headers={"Authorization": jwt_access_token})

        if resp.status_code == 200:
            data = resp.json()
            if 'entry' in data:
                logger.error("Got {} results for {}!".format(len(data['entry']), url))
                for fhir_group in data['entry']:
                    create_cohort(fhir_group['resource'], cohort_type="MY_ORGANIZATIONS")

                fhir_groups_ids = [e['resource']['id'] for e in data['entry']]

                if len(fhir_groups_ids) > 0:
                    # Cohort my patients
                    fhir_group = {
                        'id': ','.join([str(e) for e in fhir_groups_ids]),
                        'name': "Mes patients",
                        'quantity': sum([e['resource']['quantity'] for e in data['entry']])
                    }
                    create_cohort(fhir_group, cohort_type="MY_PATIENTS")
        else:
            logger.error('Error while sending a get request to the FHIR API ({}), '
                         'response contains: {}'.format(url, str(resp.__dict__)))
            raise HttpResponse(status=500)


@staticmethod
@shared_task
def import_cohorts_from_i2b2_background(user, jwt_access_token):
    import_cohorts_from_i2b2(user, jwt_access_token)


def import_i2b2_if_needed_else_background(user, jwt_access_token):
    count = Cohort.objects.filter(owner=user).count()
    if count == 0:
        import_cohorts_from_i2b2(user, jwt_access_token)
    else:
        current_app.send_task('cohort.tasks.import_cohorts_from_i2b2_background', (user, jwt_access_token,))

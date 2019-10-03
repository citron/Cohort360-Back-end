from random import randint

from cohort.models import Perimeter
from explorations.models import Exploration, Request, RequestQuerySnapshot, RequestQueryResult, Cohort
from requests import get

lorem_ipsum = "There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text. All the Lorem Ipsum generators on the Internet tend to repeat predefined chunks as necessary, making this the first true generator on the Internet. It uses a dictionary of over 200 Latin words, combined with a handful of model sentence structures, to generate Lorem Ipsum which looks reasonable. The generated Lorem Ipsum is therefore always free from repetition, injected humour, or non-characteristic words etc."


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

    # resp = get("https://fhir-r4-dev.eds.aphp.fr/Practitioner?_format=json&identifier={}".format(user.username),
    #            headers={"Authorization": jwt_access_token})
    #
    # if resp.status_code != 200 or not 'entry' in resp.json() or len(resp.json()['entry']) != 1:
    #     raise HttpResponse(status=500)
    #
    # id_fhir = resp.json()['entry'][0]['resource']['id']
    #
    # resp = get("https://fhir-r4-dev.eds.aphp.fr/Group?managing-entity={}".format(id_fhir),
    #            headers={"Authorization": jwt_access_token})

    # if resp.status_code == 200:

    # if not 'entry' in resp.json() or len(resp.json()['entry']) < 1:
    resp = get("https://fhir-r4-dev.eds.aphp.fr/Group?_id=21415,21417,21420,21359,21367,21369,21371,21373,21375,"
               "21894,21896,21650,21535,21537", headers={"Authorization": jwt_access_token})

    if resp.status_code == 200:
        for group in resp.json()['entry']:
            r = Request()
            r.owner = user
            r.name = group['resource']['name']
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
            rqr.result_size = group['resource']['quantity']
            rqr.save()

            c = Cohort()
            c.owner = user
            c.name = group['resource']['name']
            c.description = lorem_ipsum[
                            randint(0, int(len(lorem_ipsum) / 2)):randint(int(len(lorem_ipsum) / 2), len(lorem_ipsum))]
            c.request_query_result = rqr
            c.request_query_snapshot = rqs
            c.request = r
            c.perimeter = p1
            c.fhir_groups_ids = str(int(group['resource']['id']))
            c.save()

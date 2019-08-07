from cohort.models import Perimeter
from explorations.models import Exploration, Request, RequestQuerySnapshot, RequestQueryResult, Cohort
from requests import get

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

    resp = get("https://fhir-r4-dev.eds.aphp.fr/Group?managingEntity=me", headers={"Authorization": jwt_access_token})
    if resp.status_code == 200:
        for group in resp.json()['entry']:
            r = Request()
            r.name = "Test"
            r.description = "Test"
            r.exploration = e
            r.data_type_of_query = "PATIENT"
            r.save()

            rqs = RequestQuerySnapshot()
            rqs.request = r
            rqs.serialized_query = ""
            rqs.save()

            rqr = RequestQueryResult()
            rqr.request_query_snapshot = rqs
            rqr.request = r
            rqr.perimeter = p1
            rqr.result_size = 50
            rqr.save()

            c = Cohort()
            c.name = "Cohorte"
            c.description = "Cohorte descr"
            c.request_query_result = rqr
            c.request_query_snapshot = rqs
            c.request = r
            c.perimeter = p1
            c.fhir_group_id = 75
            c.save()

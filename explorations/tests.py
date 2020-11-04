import json
from datetime import timedelta

from django.utils import timezone
from django.utils.datetime_safe import datetime
from rest_framework import status
from rest_framework.test import force_authenticate

from accesses.models import IS_PART_OF_RELATONSHIP_ID, CONTAINS_RELATIONSHIP_ID, \
    CARE_SITE_DOMAIN_CONCEPT_ID, CareSiteHistory, get_all_level_children_cs_ids, \
    get_direct_children_cs_ids, get_direct_parent_care_site_ids, get_all_root_care_sites_ids, \
    get_all_cs_to_cs_relationships, get_current_user_roles_on_care_site, get_all_user_roles_on_care_site, \
    user_is_main_admin, get_all_current_accessible_care_sites_ids
from accesses.views import CareSiteHistoryViewset
from admin_cohort.settings import CARE_SITE_HISTORY_DOMAIN_ID_DEFAULT, MODEL_MANUAL_START_DATE_DEFAULT_ON_UPDATE, \
    MODEL_MANUAL_END_DATE_DEFAULT_ON_UPDATE
from admin_cohort.tests import BaseTests
from other_models.models import FactRelationship
from users.models import CareSite


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d


def create_caresite_ispartof_relationship(cs1: CareSite, cs2: CareSite) -> FactRelationship:
    return FactRelationship.objects.create(
        hash=0,
        domain_concept_id_1=CARE_SITE_DOMAIN_CONCEPT_ID,
        fact_id_1=cs1.care_site_id,
        domain_concept_id_2=CARE_SITE_DOMAIN_CONCEPT_ID,
        fact_id_2=cs2.care_site_id,
        relationship_concept_id=IS_PART_OF_RELATONSHIP_ID,
        row_id=0,
    )


def create_caresite_contains_relationship(cs1: CareSite, cs2: CareSite) -> FactRelationship:
    return FactRelationship.objects.create(
        hash=0,
        domain_concept_id_1=CARE_SITE_DOMAIN_CONCEPT_ID,
        fact_id_1=cs1.care_site_id,
        domain_concept_id_2=CARE_SITE_DOMAIN_CONCEPT_ID,
        fact_id_2=cs2.care_site_id,
        relationship_concept_id=CONTAINS_RELATIONSHIP_ID,
        row_id=0,
    )


class ModelsUnitTest(BaseTests):
    def setUp(self):
        #      cs
        #     /  \
        # cs11   cs12
        #   |    /   \
        # cs21 cs22 cs23
        #   | \    /  |
        # cs31 cs32 cs33
        super(ModelsUnitTest, self).setUp()
        [self.cs, self.cs11, self.cs12, self.cs21, self.cs22, self.cs23, self.cs31, self.cs32, self.cs33] \
            = [CareSite.objects.create(hash=0, row_id=0, care_site_id=_id) for _id in
               [10, 11, 12, 21, 22, 23, 31, 32, 33]]
        self.rel_31_21 = create_caresite_ispartof_relationship(self.cs31, self.cs21)
        self.rel_22_12 = create_caresite_ispartof_relationship(self.cs22, self.cs12)
        self.rel_23_12 = create_caresite_ispartof_relationship(self.cs23, self.cs12)

        self.rel_11_10 = create_caresite_ispartof_relationship(self.cs11, self.cs)
        self.rel_33_23 = create_caresite_ispartof_relationship(self.cs33, self.cs23)
        self.rel_32_23 = create_caresite_ispartof_relationship(self.cs32, self.cs23)
        self.rel_10_11 = create_caresite_contains_relationship(self.cs, self.cs11)
        self.rel_23_33 = create_caresite_contains_relationship(self.cs23, self.cs33)
        self.rel_23_32 = create_caresite_contains_relationship(self.cs23, self.cs32)

        self.rel_11_21 = create_caresite_contains_relationship(self.cs11, self.cs21)
        self.rel_21_32 = create_caresite_contains_relationship(self.cs21, self.cs32)
        self.rel_10_12 = create_caresite_contains_relationship(self.cs, self.cs12)

        self.cs_history_10_admin = CareSiteHistory.objects.create(
            hash=0,
            care_site_history_id=10,
            row_id=0,
            care_site_id=self.cs.care_site_id,
            role_id=self.main_admin_role.role_id,
            entity_id=self.admin_provider.provider_id,
        )
        self.cs_history_12_1_loc_admin = CareSiteHistory.objects.create(
            hash=0,
            care_site_history_id=1210,
            row_id=0,
            care_site_id=self.cs12.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id,
        )
        self.cs_history_12_1_pseudo = CareSiteHistory.objects.create(
            hash=0,
            care_site_history_id=1211,
            row_id=0,
            care_site_id=self.cs12.care_site_id,
            role_id=self.pseudo_anonymised_data_role.role_id,
            entity_id=self.provider1.provider_id,
        )
        self.cs_history_33_1_nominative = CareSiteHistory.objects.create(
            hash=0,
            care_site_history_id=331,
            row_id=0,
            care_site_id=self.cs33.care_site_id,
            role_id=self.nominative_data_role.role_id,
            entity_id=self.provider1.provider_id,
        )
        self.cs_history_23_1_outdated = CareSiteHistory.objects.create(
            hash=0,
            care_site_history_id=2310,
            row_id=0,
            care_site_id=self.cs23.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id,
            end_date=datetime.now() - timedelta(days=2)
        )
        self.cs_history_23_1_not_started = CareSiteHistory.objects.create(
            hash=0,
            care_site_history_id=2311,
            row_id=0,
            care_site_id=self.cs23.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id,
            start_date=datetime.now() + timedelta(days=2)
        )
        self.cs_history_21_1_not_started = CareSiteHistory.objects.create(
            hash=0,
            care_site_history_id=211,
            row_id=0,
            care_site_id=self.cs23.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id,
            start_date=datetime.now() + timedelta(days=2)
        )
        self.deleted_cs = CareSiteHistory.objects.create(
            hash=0,
            care_site_history_id=999,
            row_id=0,
            care_site_id=self.cs23.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id,
            start_date=datetime.now() + timedelta(days=2),
            delete_datetime=timezone.now()
        )

    def check_cs_list(self, cs_found, cs_to_find):
        cs_to_find_ids = [cs.care_site_id for cs in cs_to_find]
        msg = "\n".join(["", "got", str(cs_found), "should be", str(cs_to_find_ids)])
        for i in cs_to_find_ids:
            self.assertIn(i, cs_found, msg=msg)
        self.assertEqual(len(cs_found), len(cs_to_find), msg=msg)

    def check_rel_list(self, rel_found, rel_to_find):
        rel_to_find_ids = [rel.fact_relationship_id for rel in rel_to_find]
        msg = "\n".join(["", "got", str(rel_found), "should be", str(rel_to_find_ids)])
        for i in rel_to_find_ids:
            self.assertIn(i, rel_found, msg=msg)
        self.assertEqual(len(rel_found), len(rel_to_find), msg=msg)

    def check_role_list(self, roles_found, roles_to_find):
        roles_found_ids = [r.role_id for r in roles_found]
        roles_to_find_ids = [role.role_id for role in roles_to_find]
        msg = "\n".join(["", "got", str(roles_found_ids), "should be", str(roles_to_find_ids)])
        for i in roles_to_find_ids:
            self.assertIn(i, roles_found_ids, msg=msg)
        self.assertEqual(len(roles_found), len(roles_to_find), msg=msg)

    def test_not_retrieve_deleted_objects(self):
        cs_hs = CareSiteHistory.objects.all()
        self.assertNotIn(self.deleted_cs.care_site_history_id, [cs_h.care_site_history_id for cs_h in cs_hs])

        cs_h = CareSiteHistory.objects.filter(
            care_site_history_id=self.deleted_cs.care_site_history_id).first()
        self.assertIsNone(cs_h)

        self.assertRaises(
            CareSiteHistory.DoesNotExist,
            CareSiteHistory.objects.get,
            care_site_history_id=self.deleted_cs.care_site_history_id)

    def test_retrieve_deleted_objects_with_arg_even_deleted(self):
        cs_hs = CareSiteHistory.objects.all(even_deleted=True)
        self.assertIn(self.deleted_cs.care_site_history_id, [cs_h.care_site_history_id for cs_h in cs_hs])

        cs_h = CareSiteHistory.objects.filter(even_deleted=True,
                                              care_site_history_id=self.deleted_cs.care_site_history_id).first()
        self.assertIsNotNone(cs_h)

        cs_h = CareSiteHistory.objects.get(even_deleted=True,
                                           care_site_history_id=self.deleted_cs.care_site_history_id)
        self.assertIsNotNone(cs_h)

    def test_user_admin_is_main_admin(self):
        self.assertTrue(user_is_main_admin(self.admin_provider.provider_id))

    def test_user_admin_is_main_admin_with_manual_dates(self):
        self.cs_history_10_admin.start_date = datetime.now().date() + timedelta(days=2)
        self.cs_history_10_admin.end_date = datetime.now().date() + timedelta(days=3)
        self.cs_history_10_admin.save()
        self.assertFalse(user_is_main_admin(self.admin_provider.provider_id))

        self.cs_history_10_admin.manual_start_date = datetime.now().date() - timedelta(days=2)
        self.cs_history_10_admin.manual_end_date = datetime.now().date() + timedelta(days=2)
        self.cs_history_10_admin.save()
        self.assertTrue(user_is_main_admin(self.admin_provider.provider_id))

        self.cs_history_10_admin.manual_start_date = datetime.now().date() - timedelta(days=2)
        self.cs_history_10_admin.manual_end_date = None
        self.cs_history_10_admin.save()
        self.assertTrue(user_is_main_admin(self.admin_provider.provider_id))

        self.cs_history_10_admin.end_date = None
        self.cs_history_10_admin.save()
        self.assertTrue(user_is_main_admin(self.admin_provider.provider_id))

        self.cs_history_10_admin.end_date = datetime.now().date() - timedelta(days=1)
        self.cs_history_10_admin.save()
        self.assertFalse(user_is_main_admin(self.admin_provider.provider_id))

        self.cs_history_10_admin.end_date = datetime.now().date() + timedelta(days=3)
        self.cs_history_10_admin.save()
        self.assertTrue(user_is_main_admin(self.admin_provider.provider_id))

    def test_user_1_is_not_main_admin(self):
        self.assertFalse(user_is_main_admin(self.provider1.provider_id))

    def test_get_all_cs_to_cs_relationships(self):
        rel_found = get_all_cs_to_cs_relationships()
        rel_found = [rel.fact_relationship_id for rel in rel_found.all()]
        rel_to_find = [self.rel_31_21, self.rel_22_12, self.rel_23_12, self.rel_11_10, self.rel_33_23,
                       self.rel_32_23, self.rel_10_11, self.rel_23_33, self.rel_23_32, self.rel_11_21,
                       self.rel_21_32, self.rel_10_12, self.hospital_1_part_of_aphp_relationship,
                       self.hospital_2_part_of_aphp_relationship, self.hospital_2_contains_3_relationship]
        self.check_rel_list(rel_found, rel_to_find)

    def test_get_direct_children_cs_ids_0(self):
        cs_found = get_direct_children_cs_ids(care_site_id=self.cs.care_site_id)
        cs_to_find = [self.cs11, self.cs12]
        self.check_cs_list(cs_found, cs_to_find)

    def test_get_all_level_children_cs_ids_12(self):
        cs_found = get_all_level_children_cs_ids(care_site_ids=self.cs12.care_site_id)
        cs_to_find = [self.cs12, self.cs22, self.cs23, self.cs32, self.cs33]
        self.check_cs_list(cs_found, cs_to_find)

    def test_get_all_level_children_cs_ids_11_23(self):
        cs_found = get_all_level_children_cs_ids(care_site_ids=[self.cs11.care_site_id, self.cs23.care_site_id])
        cs_to_find = [self.cs11, self.cs21, self.cs23, self.cs31, self.cs32, self.cs33]
        self.check_cs_list(cs_found, cs_to_find)

    def test_get_direct_parent_care_site_ids_32(self):
        cs_found = get_direct_parent_care_site_ids(care_site_id=self.cs32.care_site_id)
        cs_to_find = [self.cs21, self.cs23]
        self.check_cs_list(cs_found, cs_to_find)

    def test_get_all_root_care_sites_ids_32(self):
        cs_found = get_all_root_care_sites_ids(care_site_ids=self.cs32.care_site_id)
        cs_to_find = [self.cs32, self.cs21, self.cs23, self.cs11, self.cs12, self.cs]
        self.check_cs_list(cs_found, cs_to_find)

    def test_get_all_root_care_sites_ids_21_23(self):
        cs_found = get_all_root_care_sites_ids(care_site_ids=[self.cs21.care_site_id, self.cs23.care_site_id])
        cs_to_find = [self.cs21, self.cs23, self.cs11, self.cs12, self.cs]
        self.check_cs_list(cs_found, cs_to_find)

    def test_get_current_user_1_access_on_care_site_12(self):
        roles_found = get_current_user_roles_on_care_site(provider_id=self.provider1.provider_id,
                                                          care_site_id=self.cs12.care_site_id)
        roles_to_find = [self.local_admin_role, self.pseudo_anonymised_data_role]
        self.check_role_list(roles_found, roles_to_find)

    def test_get_current_user_1_access_on_care_site_23(self):
        roles_found = get_current_user_roles_on_care_site(provider_id=self.provider1.provider_id,
                                                          care_site_id=self.cs23.care_site_id)
        roles_to_find = []
        self.check_role_list(roles_found, roles_to_find)

    def test_get_all_user_admin_roles_on_care_site_10(self):
        roles_found = get_all_user_roles_on_care_site(provider_id=self.admin_provider.provider_id,
                                                      care_site_id=self.cs.care_site_id)
        roles_to_find = [self.main_admin_role]
        self.check_role_list(roles_found, roles_to_find)

    def test_get_all_user_admin_roles_on_care_site_31(self):
        roles_found = get_all_user_roles_on_care_site(provider_id=self.admin_provider.provider_id,
                                                      care_site_id=self.cs31.care_site_id)
        roles_to_find = [self.main_admin_role]
        self.check_role_list(roles_found, roles_to_find)

    def test_get_all_user_1_roles_on_care_site_1(self):
        roles_found = get_all_user_roles_on_care_site(provider_id=self.provider1.provider_id,
                                                      care_site_id=self.cs.care_site_id)
        roles_to_find = []
        self.check_role_list(roles_found, roles_to_find)

    def test_get_all_user_1_roles_on_care_site_31(self):
        roles_found = get_all_user_roles_on_care_site(provider_id=self.provider1.provider_id,
                                                      care_site_id=self.cs31.care_site_id)
        roles_to_find = []
        self.check_role_list(roles_found, roles_to_find)

    def test_get_all_user_1_roles_on_care_site_32(self):
        roles_found = get_all_user_roles_on_care_site(provider_id=self.provider1.provider_id,
                                                      care_site_id=self.cs32.care_site_id)
        roles_to_find = [self.local_admin_role, self.pseudo_anonymised_data_role]
        self.check_role_list(roles_found, roles_to_find)

    def test_get_all_user_1_roles_on_care_site_33(self):
        roles_found = get_all_user_roles_on_care_site(provider_id=self.provider1.provider_id,
                                                      care_site_id=self.cs33.care_site_id)
        roles_to_find = [self.local_admin_role, self.pseudo_anonymised_data_role, self.nominative_data_role]
        self.check_role_list(roles_found, roles_to_find)

    def test_get_all_current_accessible_care_sites_ids_admin(self):
        cs_found = get_all_current_accessible_care_sites_ids(provider_id=self.admin_provider.provider_id)
        cs_to_find = [self.cs, self.cs11, self.cs12, self.cs21, self.cs22, self.cs23, self.cs31, self.cs32, self.cs33]
        self.check_cs_list(cs_found, cs_to_find)

    def test_get_all_current_accessible_care_sites_ids_1(self):
        cs_found = get_all_current_accessible_care_sites_ids(provider_id=self.provider1.provider_id)
        cs_to_find = [self.cs12, self.cs22, self.cs23, self.cs32, self.cs33]
        self.check_cs_list(cs_found, cs_to_find)

    def test_get_all_current_accessible_care_sites_ids_2(self):
        cs_found = get_all_current_accessible_care_sites_ids(provider_id=self.provider2.provider_id)
        cs_to_find = []
        self.check_cs_list(cs_found, cs_to_find)


class CareSiteHistoryTests(BaseTests):
    unupdatable_fields = ["role_id", "start_date", "end_date", "care_site_id", "entity_id"]
    unsettable_default_fields = dict(
        change_datetime=None,
        role_source_id=None,
        role_source_value=None,
        cdm_source=None,
        domain_id=CARE_SITE_HISTORY_DOMAIN_ID_DEFAULT,
        relationship_type_concept_id=None,
    )
    unsettable_fields = ["care_site_history_id"]

    def setUp(self):
        super(CareSiteHistoryTests, self).setUp()
        #         main_admin(aphp)
        #        /    \
        # u1admin(h1)  u2pseudo+admin(h2)
        #                |
        #             u1pseudo(h3)
        self.admin_access = CareSiteHistory.objects.create(
            hash=0,
            row_id=0,
            care_site_id=self.aphp.care_site_id,
            role_id=self.main_admin_role.role_id,
            entity_id=self.admin_provider.provider_id,
        )
        self.access_user1_admin_h1 = CareSiteHistory.objects.create(
            hash=0,
            row_id=0,
            care_site_id=self.hospital1.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id,
        )
        self.access_user1_pseudo_h3 = CareSiteHistory.objects.create(
            hash=0,
            row_id=0,
            care_site_id=self.hospital3.care_site_id,
            role_id=self.pseudo_anonymised_data_role.role_id,
            entity_id=self.provider1.provider_id,
        )
        self.access_user2_pseudo_h2 = CareSiteHistory.objects.create(
            hash=0,
            row_id=0,
            care_site_id=self.hospital2.care_site_id,
            role_id=self.pseudo_anonymised_data_role.role_id,
            entity_id=self.provider2.provider_id,
        )
        self.access_user2_admin_h2 = CareSiteHistory.objects.create(
            hash=0,
            row_id=0,
            care_site_id=self.hospital2.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider2.provider_id,
        )


class CareSiteHistoryGetTests(CareSiteHistoryTests):
    def check_cs_histories_response(self, response, csh_to_find):
        csh_found = [ObjectView(csh) for csh in self.get_response_payload(response)["results"]]

        csh_found_ids = [cs.care_site_history_id for cs in csh_found]
        csh_to_find_ids = [cs.care_site_history_id for cs in csh_to_find]
        msg = "\n".join(["", "got", str(csh_found_ids), "should be", str(csh_to_find_ids)])
        for i in csh_to_find_ids:
            self.assertIn(i, csh_found_ids, msg=msg)
        self.assertEqual(len(csh_found_ids), len(csh_to_find), msg=msg)

    def setUp(self):
        self.list_view = CareSiteHistoryViewset.as_view({'get': 'list'})
        self.retrieve_view = CareSiteHistoryViewset.as_view({'get': 'retrieve'})
        return super(CareSiteHistoryGetTests, self).setUp()

    def test_admin_get_all_users(self):
        # As a main admin, I can get all care_site_histories
        request = self.factory.get('/accesses')
        force_authenticate(request, self.admin_user)
        response = self.list_view(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        csh_to_find = [self.admin_access, self.access_user2_pseudo_h2, self.access_user1_pseudo_h3,
                       self.access_user2_admin_h2, self.access_user1_admin_h1]
        self.check_cs_histories_response(response, csh_to_find)

    # not used currently
    def test_user2_get_simple_accesses_where_local_admin_with_children_cs(self):
        # As a local admin on hospital2, I can get care_site_histories simple accesses of hospital2 and hospital3
        request = self.factory.get('/accesses', data=dict(type="user"))
        force_authenticate(request, self.user2)
        response = self.list_view(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        csh_to_find = [self.access_user2_pseudo_h2, self.access_user1_pseudo_h3]
        self.check_cs_histories_response(response, csh_to_find)

    # not used currently
    def test_user2_get_admin_accesses_where_local_admin_with_children_cs(self):
        # As a local admin on hospital2, I can get care_site_histories of admins of hospital2 and hospital3
        request = self.factory.get('/accesses', data=dict(type="admin"))
        force_authenticate(request, self.user2)
        response = self.list_view(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        csh_to_find = [self.access_user2_admin_h2]
        self.check_cs_histories_response(response, csh_to_find)

    def test_user2_get_all_accesses_where_local_admin_with_children_cs(self):
        # As a local admin on hospital2, I can get care_site_histories of hospital2 and hospital3
        request = self.factory.get('/accesses')
        force_authenticate(request, self.user2)
        response = self.list_view(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        csh_to_find = [self.access_user2_pseudo_h2, self.access_user1_pseudo_h3,
                       self.access_user2_admin_h2]
        self.check_cs_histories_response(response, csh_to_find)

    def test_user1_get_all_accesses_where_local_admin_with_children_cs(self):
        # As a local admin on hospital1, I can get care_site_histories of only hospital1
        request = self.factory.get('/accesses')
        force_authenticate(request, self.user1)
        response = self.list_view(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        csh_to_find = [self.access_user1_admin_h1]
        self.check_cs_histories_response(response, csh_to_find)

    def test_user2_get_csh_with_id_as_local_admin_h3(self):
        # As a local admin on hospital2, I can get a specific care_site_history on hospital3
        request = self.factory.get(f"/accesses")
        force_authenticate(request, self.user2)
        response = self.retrieve_view(
            request,
            care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        csh_found = ObjectView(self.get_response_payload(response))
        self.assertEqual(csh_found.care_site_history_id, self.access_user1_pseudo_h3.care_site_history_id)
        self.assertEqual(ObjectView(csh_found.role).role_id, self.pseudo_anonymised_data_role.role_id)
        self.assertEqual(ObjectView(csh_found.provider).provider_id, self.provider1.provider_id)
        self.assertEqual(ObjectView(csh_found.care_site).care_site_id, self.hospital3.care_site_id)

    def test_error_user1_get_csh_with_id_on_wrong_cs(self):
        # As a local admin on hospital1, I cannot get a specific care_site_history on hospital2
        request = self.factory.get(f"/accesses")
        force_authenticate(request, self.user1)
        response = self.retrieve_view(
            request,
            care_site_history_id=self.access_user2_pseudo_h2.care_site_history_id)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_user2_get_csh_with_id_as_local_admin_h3_with_manual_data(self):
        # As a local admin on hospital2, I can get a specific care_site_history on hospital3
        # but manual_columns before the original ones
        start_date = datetime.now().date()
        old_end_date = datetime.now().date() + timedelta(days=2)
        manual_end_date = datetime.now().date() + timedelta(days=4)
        new_csh = CareSiteHistory.objects.create(
            hash=0,
            row_id=0,
            care_site_id=self.hospital3.care_site_id,
            role_id=self.pseudo_anonymised_data_role.role_id,
            entity_id=self.admin_provider.provider_id,
            start_date=start_date,
            end_date=old_end_date,
            manual_end_date=manual_end_date,
        )
        request = self.factory.get(f"/accesses")
        force_authenticate(request, self.user2)
        response = self.retrieve_view(request, care_site_history_id=new_csh.care_site_history_id)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        csh_found = ObjectView(self.get_response_payload(response))
        self.assertEqual(datetime.fromisoformat(csh_found.actual_start_date).date(), start_date)
        self.assertEqual(datetime.fromisoformat(csh_found.actual_end_date).date(), manual_end_date)


class CareSiteHistoryCreateTests(CareSiteHistoryTests):
    def test_create_admin_as_main_admin(self):
        # As a main admin, I can create an admin access for user1 to hospital2
        request = self.factory.post('/accesses', dict(
            care_site_id=self.hospital2.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id), format='json')
        force_authenticate(request, self.admin_user)
        response = CareSiteHistoryViewset.as_view({'post': 'create'})(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        access = CareSiteHistory.objects.filter(care_site_id=self.hospital2.care_site_id,
                                                role_id=self.local_admin_role.role_id,
                                                entity_id=self.provider1.provider_id).first()
        self.check_is_created(access, self.admin_provider)

    def test_create_admin_as_main_admin_with_dates(self):
        # As a main admin, I can create an admin access for user1 to hospital2
        request = self.factory.post('/accesses', dict(
            care_site_id=self.hospital2.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id,
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=2)
        ),format='json')
        force_authenticate(request, self.admin_user)
        response = CareSiteHistoryViewset.as_view({'post': 'create'})(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        access = CareSiteHistory.objects.filter(care_site_id=self.hospital2.care_site_id,
                                                role_id=self.local_admin_role.role_id,
                                                entity_id=self.provider1.provider_id).first()
        self.check_is_created(access, self.admin_provider)
        self.assertEqual(access.manual_start_date, datetime.now().date(),)
        self.assertEqual(access.manual_end_date, datetime.now().date() + timedelta(days=2))

    def test_create_user_as_local_admin(self):
        # As a local admin on hospital1, I can create a user access for user2 to hospital1
        request = self.factory.post('/accesses', dict(
            care_site_id=self.hospital1.care_site_id,
            role_id=self.pseudo_anonymised_data_role.role_id,
            entity_id=self.provider2.provider_id), format='json')
        force_authenticate(request, self.user1)
        response = CareSiteHistoryViewset.as_view({'post': 'create'})(request)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        access = CareSiteHistory.objects.filter(care_site_id=self.hospital1.care_site_id,
                                                role_id=self.pseudo_anonymised_data_role.role_id,
                                                entity_id=self.provider2.provider_id).first()
        self.check_is_created(access, self.provider1)

    def test_error_create_user_as_a_user(self):
        # As user with access to hospital1, I cannot create an access for user2 to hospital3
        request = self.factory.post('/accesses', dict(
            care_site_id=self.hospital3.care_site_id,
            role_id=self.pseudo_anonymised_data_role.role_id,
            entity_id=self.provider2.provider_id), format='json')
        force_authenticate(request, self.user1)
        response = CareSiteHistoryViewset.as_view({'post': 'create'})(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
        access = CareSiteHistory.objects.filter(care_site_id=self.hospital2.care_site_id,
                                                role_id=self.pseudo_anonymised_data_role.role_id,
                                                entity_id=self.provider1.provider_id).first()
        self.assertIsNone(access)

    def test_error_create_user_from_another_care_site(self):
        # As a local admin from hospital1, I cannot create an access for user1 to hospital2
        request = self.factory.post('/accesses', dict(
            care_site_id=self.hospital2.care_site_id,
            role_id=self.pseudo_anonymised_data_role.role_id,
            entity_id=self.provider1.provider_id), format='json')
        force_authenticate(request, self.user1)
        response = CareSiteHistoryViewset.as_view({'post': 'create'})(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
        access = CareSiteHistory.objects.filter(care_site_id=self.hospital2.care_site_id,
                                                role_id=self.pseudo_anonymised_data_role.role_id,
                                                entity_id=self.provider1.provider_id).first()
        self.assertIsNone(access)

    def test_create_user_as_local_admin_from_root_care_site(self):
        # As a local admin on hospital2, I can create a user access for user2 to hospital3
        request = self.factory.post('/accesses', dict(
            care_site_id=self.hospital3.care_site_id,
            role_id=self.pseudo_anonymised_data_role.role_id,
            entity_id=self.provider2.provider_id), format='json')
        force_authenticate(request, self.user2)
        response = CareSiteHistoryViewset.as_view({'post': 'create'})(request)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        access = CareSiteHistory.objects.filter(care_site_id=self.hospital3.care_site_id,
                                                role_id=self.pseudo_anonymised_data_role.role_id,
                                                entity_id=self.provider2.provider_id).first()
        self.check_is_created(access, self.provider2)

    def test_create_admin_as_main_admin_but_without_unsettable_fields(self):
        # As a main admin, I can create an admin access for user1 to hospital2
        request_csh = dict(
            care_site_id=self.hospital2.care_site_id,
            role_id=self.local_admin_role.role_id,
            entity_id=self.provider1.provider_id,
            change_datetime=datetime.now().date(),
            role_source_id=50,
            role_source_value="test",
            cdm_source="test",
            domain_id="test",
            relationship_type_concept_id=50,
            care_site_history_id=50,
        )
        request = self.factory.post('/accesses', request_csh, format='json')
        force_authenticate(request, self.admin_user)
        response = CareSiteHistoryViewset.as_view({'post': 'create'})(request)
        response.render()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        access = CareSiteHistory.objects.filter(care_site_id=self.hospital2.care_site_id,
                                                role_id=self.local_admin_role.role_id,
                                                entity_id=self.provider1.provider_id).first()
        self.check_is_created(access, self.admin_provider, request_csh)


class CareSiteHistoryDeleteTests(CareSiteHistoryTests):
    def setUp(self):
        self.view = CareSiteHistoryViewset.as_view({'delete': 'destroy'})
        return super(CareSiteHistoryDeleteTests, self).setUp()

    def test_delete_user_as_main_admin(self):
        # As an admin on main care_site, I can delete a user access for user to hospital2
        request = self.factory.delete(f"/accesses")
        force_authenticate(request, self.admin_user)
        response = self.view(request, care_site_history_id=self.access_user2_pseudo_h2.care_site_history_id)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        access = CareSiteHistory.objects.filter(
            even_deleted=True,
            care_site_history_id=self.access_user2_pseudo_h2.care_site_history_id).first()
        self.check_is_deleted(access, self.admin_provider)

    def test_delete_user_as_local_admin(self):
        # As a local admin on hospital2, I can delete a user access for user2 to hospital2
        request = self.factory.delete(f"/accesses")
        force_authenticate(request, self.user2)
        response = self.view(request, care_site_history_id=self.access_user2_pseudo_h2.care_site_history_id)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        access = CareSiteHistory.objects.filter(
            even_deleted=True,
            care_site_history_id=self.access_user2_pseudo_h2.care_site_history_id).first()
        self.check_is_deleted(access, self.provider2)

    def test_delete_user_as_local_admin_on_root_caresite(self):
        # As a local admin on hospital2, I can delete a user access for user1 to hospital3
        request = self.factory.delete(f"/accesses")
        force_authenticate(request, self.user2)
        response = self.view(request, care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        access = CareSiteHistory.objects.filter(
            even_deleted=True,
            care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id).first()
        self.check_is_deleted(access, self.provider2)

    def test_error_delete_user_as_local_admin_on_wrong_hospital(self):
        # As a local admin on hospital1, I can't delete a user access for user2 to hospital2
        request = self.factory.delete(f"/accesses")
        force_authenticate(request, self.user1)
        response = self.view(request, care_site_history_id=self.access_user2_pseudo_h2.care_site_history_id)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
        access = CareSiteHistory.objects.filter(
            even_deleted=True,
            care_site_history_id=self.access_user2_pseudo_h2.care_site_history_id).first()
        self.assertIsNotNone(access)
        self.assertIsNone(access.delete_datetime)


class CareSiteHistoryUpdateTests(CareSiteHistoryTests):
    def setUp(self):
        self.view = CareSiteHistoryViewset.as_view({'patch': 'partial_update'})
        return super(CareSiteHistoryUpdateTests, self).setUp()

    def test_update_user_access_as_main_admin(self):
        # As an admin on main care_site, I can update a user access for user1 to hospital3
        # but role_id, care_site_id, and entity_id won't change
        request = self.factory.patch(f"/accesses", dict(
            role_id=self.nominative_data_role.role_id,
            care_site_id=self.hospital2.care_site_id,
            entity_id=self.provider2.provider_id,
            end_date=datetime.now().date() + timedelta(days=2)
        ), format='json')
        force_authenticate(request, self.admin_user)
        origin_role_id = self.access_user1_pseudo_h3.role_id

        response = self.view(request, care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        access = CareSiteHistory.objects.get(care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)
        self.check_unupdatable_not_updated(access, self.access_user1_pseudo_h3)

        self.assertEqual(access.manual_end_date, datetime.now().date() + timedelta(days=2))
        self.assertEqual(access.role_id, origin_role_id)

    def test_update_user_access_as_local_admin(self):
        # As a local admin on hospital2, I can update a user access for user1 to hospital3
        request = self.factory.patch(f"/accesses", dict(
            start_date=datetime.now().date() + timedelta(days=2)), format='json')
        force_authenticate(request, self.user2)
        response = self.view(request, care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        access = CareSiteHistory.objects.get(care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)
        self.check_unupdatable_not_updated(access, self.access_user1_pseudo_h3)

        self.assertEqual(access.manual_start_date, datetime.now().date() + timedelta(days=2))

    def test_error_update_user_access_other_caresite(self):
        # As a local admin on hospital1, I can't update a user access for user2 to hospital2
        request = self.factory.patch(f"/accesses", dict(
            start_date=datetime.now().date() + timedelta(days=2)), format='json')
        force_authenticate(request, self.user1)
        response = self.view(request, care_site_history_id=self.access_user2_pseudo_h2.care_site_history_id)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
        access = CareSiteHistory.objects.get(care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)
        self.check_unupdatable_not_updated(access, self.access_user1_pseudo_h3)

        self.assertNotEqual(access.manual_start_date, datetime.now().date() + timedelta(days=2))

    def test_update_with_dates_as_none_retrieve_constants(self):
        # As an admin on main care_site, I can update a user access for user1 to hospital3
        # but if None or undefined, manual_dates will be set to constants defined in settings
        request = self.factory.patch(f"/accesses", dict(
            start_date=None,
            end_date=None
        ), format='json')
        force_authenticate(request, self.admin_user)

        response = self.view(request, care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)

        response.render()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        access = CareSiteHistory.objects.get(care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)
        self.check_unupdatable_not_updated(access, self.access_user1_pseudo_h3)

        self.assertEqual(access.manual_start_date, MODEL_MANUAL_START_DATE_DEFAULT_ON_UPDATE.date())
        self.assertEqual(access.manual_end_date, MODEL_MANUAL_END_DATE_DEFAULT_ON_UPDATE.date())


    # used to be when it was possible to update role_id
    # def test_error_upgrade_user_access_as_local_admin(self):
    #     # As a local admin on hospital2, I can't upgrade a user access for user1 in hospital3 to admin access
    #     request = self.factory.patch(f"/accesses", dict(
    #         start_date=datetime.now().date() + timedelta(days=2)), format='json')
    #     force_authenticate(request, self.user2)
    #     response = CareSiteHistoryViewset \
    #         .as_view({'patch': 'partial_update'})(request, pk=self.access_user1_pseudo_h3.care_site_history_id)
    #
    #     response.render()
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
    #     access = CareSiteHistory.objects.get(care_site_history_id=self.access_user1_pseudo_h3.care_site_history_id)
    #     self.check_unupdatable_not_updated(access, self.access_user1_pseudo_h3)
    #
    #     self.assertNotEqual(access.manual_start_date, datetime.now().date() + timedelta(days=2))
    #
    # def test_error_downgrade_admin_access_as_local_admin(self):
    #     # As a local admin on hospital1, I can't update an admin access for user2 in hospital2 to user role
    #     access_user2_admin_h1 = CareSiteHistory.objects.create(
    #         hash=0,
    #         row_id=0,
    #         care_site_id=self.hospital1.care_site_id,
    #         role_id=self.nominative_data_role.role_id,
    #         entity_id=self.provider2.provider_id,
    #         manual_role_id=self.local_admin_role.role_id
    #     )
    #     request = self.factory.patch(f"/accesses", dict(
    #         role_id=self.nominative_data_role.role_id, format='json'))
    #     force_authenticate(request, self.user1)
    #     response = CareSiteHistoryViewset \
    #         .as_view({'patch': 'partial_update'})(request, pk=access_user2_admin_h1.care_site_history_id)
    #
    #     response.render()
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
    #     access = CareSiteHistory.objects.get(care_site_history_id=access_user2_admin_h1.care_site_history_id)
    #     self.check_unupdatable_not_updated(access, self.access_user2_admin_h1)
    #
    #     self.assertEqual(access.manual_role_id, self.local_admin_role.role_id)

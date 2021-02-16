import json

from django.test import TestCase, Client
from rest_framework.test import APIRequestFactory

from cohort.models import User
from cohort_back.models import BaseModel
from cohort_back.celery import app as celery_app


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d


class BaseTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = Client()  # useful for nested urls tests, because it uses reverse() function
        celery_app.conf.update(CELERY_ALWAYS_EAGER=True)

        # USERS
        self.user1 = User.objects.create(
            username="0000001",
            email="zt@terra.org",
            is_active=True,
            firstname="Zidane",
            lastname="Tribal",
        )
        self.user2 = User.objects.create(
            username="0000002",
            email="bibi@hera.org",
            is_active=True,
            firstname="Bi",
            lastname="Bi",
        )

    def get_response_payload(self, response):
        response.render()
        return json.loads(response.content)

    def check_get_response(self, response, obj_to_find):
        obj_found = [ObjectView(res) for res in self.get_response_payload(response)["results"]] if \
            isinstance(obj_to_find, list) else [ObjectView(self.get_response_payload(response))]
        obj_found_ids = [str(obj.uuid) for obj in obj_found]

        obj_to_find = obj_to_find if isinstance(obj_to_find, list) else [obj_to_find]
        obj_to_find_ids = [str(obj.uuid) for obj in obj_to_find]

        msg = "\n".join(["", "got", str(obj_found_ids), "should be", str(obj_to_find_ids)])
        for i in obj_to_find_ids:
            self.assertIn(i, obj_found_ids, msg=msg)
        self.assertEqual(len(obj_found_ids), len(obj_to_find), msg=msg)

    def check_is_created(self, base_instance, owner, request_model=dict()):
        self.assertTrue(isinstance(base_instance, BaseModel))
        self.assertIsNotNone(base_instance)

        [self.assertEqual(getattr(base_instance, f), v, f"Error with model's {f}")
         for [f, v] in self.unsettable_default_fields.items()]

        if len(request_model.items()) > 0:
            [self.assertNotEqual(getattr(base_instance, f), request_model.get(f), f"Error with model's {f}")
             for f in self.unsettable_fields]

        self.assertEqual(base_instance.owner_id, owner.uuid)

        for dupp_field in self.manual_dupplicated_fields:
            self.assertIsNone(getattr(base_instance, dupp_field))
            if dupp_field in request_model:
                manual_field = f"manual_{dupp_field}"
                self.assertEqual(getattr(base_instance, manual_field), request_model[dupp_field],
                                 f"Error with model's {dupp_field}")

    def check_is_deleted(self, base_instance, provider):
        self.assertTrue(isinstance(base_instance, BaseModel))
        self.assertIsNotNone(base_instance)
        self.assertIsNotNone(base_instance.delete_datetime)
        self.assertEqual(base_instance.entry_deleted_by, provider.provider_id)

    # def check_unupdatable_not_updated(self, base_instance, originModel, request_model=dict()):
    #     self.assertTrue(isinstance(base_instance, BaseModel))
    #     self.assertTrue(isinstance(originModel, BaseModel))
    #     [self.assertNotEqual(getattr(base_instance, f), request_model[f], f"Error with model's {f}")
    #      for f in self.unupdatable_fields + self.manual_dupplicated_fields if f in request_model]
    #
    #     for dupp_field in self.manual_dupplicated_fields:
    #         if dupp_field in request_model:
    #             manual_field = f"manual_{dupp_field}"
    #             self.assertEqual(getattr(base_instance, manual_field), request_model[dupp_field])

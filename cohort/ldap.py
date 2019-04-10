from ldap3 import Connection

from cohort_back.settings import LDAP_CONNECTION_PARAMETERS, LDAP_CONNECTION, LDAP_BASE_DN, LDAP_SEARCH_FILTER, \
    LDAP_SEARCH_SCOPE, LDAP_DISPLAY_NAME_ATTR, LDAP_USERNAME_ATTR, LDAP_FIRSTNAME_ATTR, LDAP_LASTNAME_ATTR, \
    LDAP_EMAIL_ATTR, LDAP_AUTH_USERNAME


class TooFewSearchResults(Exception):
    pass


class LDAP:
    @staticmethod
    def check_ids(username, password):
        temp_co = Connection(
            user=LDAP_AUTH_USERNAME.format(username),
            password=password,
            **LDAP_CONNECTION_PARAMETERS,
        )
        temp_co.bind()
        temp_co.unbind()

        return temp_co.result['result'] == 0

    @staticmethod
    def user_info(username):
        LDAP_CONNECTION.search(
            search_base=LDAP_BASE_DN,
            search_filter=LDAP_SEARCH_FILTER.format(username),
            search_scope=LDAP_SEARCH_SCOPE,
            attributes=[
                LDAP_DISPLAY_NAME_ATTR,
                LDAP_USERNAME_ATTR,
                LDAP_FIRSTNAME_ATTR,
                LDAP_LASTNAME_ATTR,
                LDAP_EMAIL_ATTR,
            ],
        )

        if LDAP_CONNECTION.result['result'] == 0 and len(LDAP_CONNECTION.entries) == 1:
            result = LDAP_CONNECTION.response[0]

            return {
                "displayname": result["attributes"][LDAP_DISPLAY_NAME_ATTR],
                "username": result["attributes"][LDAP_USERNAME_ATTR],
                "firstname": result["attributes"][LDAP_FIRSTNAME_ATTR],
                "lastname": result["attributes"][LDAP_LASTNAME_ATTR],
                "email": result["attributes"][LDAP_EMAIL_ATTR],
            }

        raise TooFewSearchResults()

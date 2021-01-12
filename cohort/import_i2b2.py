import psycopg2 as psycopg2

from cohort_back.settings import PG_OMOP_URL, PG_OMOP_USER, PG_OMOP_PASS, PG_OMOP_DBNAME, PG_OMOP_SCHEMA, DEBUG


def get_one(sql):
    conn = psycopg2.connect(
        host=PG_OMOP_URL,
        database=PG_OMOP_DBNAME,
        user=PG_OMOP_USER,
        password=PG_OMOP_PASS,
        options='-c search_path={}'.format(PG_OMOP_SCHEMA))
    c = conn.cursor()
    try:
        c.execute(sql)
        rows = c.fetchall()
    except psycopg2.Error as e:
        if DEBUG:
            raise Exception(
                "Failed to retrieve cohort information from OMOP Postgres instance! SQL: {} Error: {}".format(sql,
                                                                                                              str(e)))
        raise Exception("Code errored! Internal 4558712.")
    finally:
        conn.close()
    count = len(rows)
    if count == 1:
        return rows[0][0]
    if count > 1:
        raise ValueError("Code errored! Internal 4558713.")
    return None


def get_multiple(sql):
    conn = psycopg2.connect(
        host=PG_OMOP_URL,
        database=PG_OMOP_DBNAME,
        user=PG_OMOP_USER,
        password=PG_OMOP_PASS,
        options='-c search_path={}'.format(PG_OMOP_SCHEMA))
    c = conn.cursor()
    try:
        c.execute(sql)
        rows = c.fetchall()
    except psycopg2.Error as e:
        if DEBUG:
            raise Exception(
                "Failed to retrieve cohort information from OMOP Postgres instance! Error: {}".format(str(e)))
        raise Exception("Code errored! Internal 4558712.")
    finally:
        conn.close()
    count = len(rows)
    if count < 1:
        return None
    return rows


class OmopCohort:
    def __init__(self, sql_omop_res: any):
        self.fhir_id = sql_omop_res[0]
        self.name = sql_omop_res[1]
        self.description = sql_omop_res[2]
        self.creation_date = sql_omop_res[3]
        self.size = sql_omop_res[4]
        self.username = sql_omop_res[5]


def get_users_cohorts(users_ids_aph: [str]) -> [OmopCohort]:
    tmp = get_multiple(
        """
        SELECT cd.cohort_definition_id, cd.cohort_definition_name, cd.cohort_definition_description,
            cd.cohort_initiation_datetime, cd.cohort_size,
            p.provider_source_value
        FROM cohort_definition cd 
            JOIN provider p ON p.provider_id=cd.owner_entity_id 
        WHERE cd.owner_domain_id='Provider' 
            AND p.provider_source_value IN ({})
            AND p.delete_datetime IS NULL
            AND cd.cohort_size>0
        """.format(", ".join([f"'{id}'" for id in users_ids_aph]))
    )
    if tmp is None:
        return []
    res = []
    for t in tmp:
        res.append(OmopCohort(t))
    return res


class OmopCareSiteCohort:
    def __init__(self, sql_omop_res: any):
        self.fhir_id = sql_omop_res[0]
        self.name = sql_omop_res[1]
        self.cs_start_date = sql_omop_res[2]
        self.cs_end_date = sql_omop_res[3]
        self.cs_manual_start_date = sql_omop_res[4]
        self.cs_manual_end_date = sql_omop_res[5]
        self.size = sql_omop_res[6]
        self.care_site_id = sql_omop_res[7]
        self.p_valid_start_datetime = sql_omop_res[8]
        self.p_valid_end_datetime = sql_omop_res[9]
        self.p_manual_valid_start_datetime = sql_omop_res[10]
        self.p_manual_valid_end_datetime = sql_omop_res[11]
        self.right_read_data_nominative = sql_omop_res[12]
        self.right_read_data_pseudo_anonymised = sql_omop_res[13]
        self.username = sql_omop_res[14]
        self.creation_date = None


def get_user_care_sites_cohorts(users_ids_aph: [str]) -> [OmopCareSiteCohort]:
    tmp = get_multiple(
        """
        SELECT cd.cohort_definition_id,
            cs.care_site_name, cs.start_date, cs.end_date, cs.manual_start_date, cs.manual_end_date,
            cd.cohort_size,
            cd.owner_entity_id,
            p.valid_start_datetime, p.valid_end_datetime, p.manual_valid_start_datetime, p.manual_valid_end_datetime,
            r.right_read_data_nominative, r.right_read_data_pseudo_anonymised,
            p.provider_source_value
        FROM care_site cs
            JOIN care_site_history csh on cs.care_site_id=csh.care_site_id 
            JOIN provider p on p.provider_id=csh.entity_id 
            JOIN cohort_definition cd on cd.owner_entity_id=cs.care_site_id
            JOIN role r on r.role_id=csh.role_id
        WHERE p.provider_source_value IN ({})
            AND p.delete_datetime IS NULL
            AND cd.owner_domain_id='Care_site'
            AND csh.domain_id='Provider'
            AND csh.delete_datetime IS NULL
        """.format(", ".join([f"'{id}'" for id in users_ids_aph]))
    )
    if tmp is None:
        return []
    res = []
    for t in tmp:
        res.append(OmopCohort(t))
    return res


def get_unique_patient_count_from_org_union(org_ids):
    if len(org_ids) == 0:
        return 0
    tmp = get_one(
        """
        SELECT COUNT(*) FROM (SELECT DISTINCT vo.person_id FROM omop.visit_occurrence vo
        WHERE vo.care_site_id IN ({})) AS temp
        """.format(','.join([str(e) for e in org_ids]))
    )
    if tmp is None:
        raise Exception("Code errored! Internal 4558714.")
    return tmp

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


def get_user_cohorts(user_id_aph):
    tmp = get_multiple(
        """
        select cd.cohort_definition_id, cd.cohort_definition_name, cd.cohort_initiation_datetime, cd.cohort_size 
        from cohort_definition cd 
        join provider p on p.provider_id=cd.owner_entity_id 
        where cd.owner_domain_id='Provider' 
        and p.provider_source_value='{}'
        and cd.cohort_size>0
        """.format(user_id_aph)
    )
    if tmp is None:
        return []
    res = []
    for t in tmp:
        res.append({
            'fhir_id': t[0],
            'name': t[1],
            'creation_date': t[2],
            'size': t[3]
        })
    return res


def get_user_care_sites_cohorts(user_id_aph):
    tmp = get_multiple(
        """
        select cd.cohort_definition_id, cs.care_site_name, cd.cohort_size, cd.owner_entity_id
        from care_site cs 
        join care_site_history csh on cs.care_site_id=csh.care_site_id 
        join provider p on p.provider_id=csh.entity_id 
        join cohort_definition cd on cd.owner_entity_id=cs.care_site_id
        where p.provider_source_value='{}'
        and cd.owner_domain_id='Care_site'
        and csh.domain_id='Provider'
        """.format(user_id_aph)
    )
    if tmp is None:
        return []
    res = []
    for t in tmp:
        res.append({
            'fhir_id': t[0],
            'name': t[1],
            'size': t[2],
            'care_site_id': t[3],
            'creation_date': None,
        })
    return res


def get_unique_patient_count_from_org_union(org_ids):
    tmp = get_one(
        """
        SELECT COUNT(*) FROM (SELECT DISTINCT vo.person_id FROM omop.visit_occurrence vo
        WHERE vo.care_site_id IN ({})) AS temp
        """.format(','.join([str(e) for e in org_ids]))
    )
    if tmp is None:
        raise Exception("Code errored! Internal 4558714.")
    return tmp

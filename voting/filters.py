import coreapi
import coreschema
from django.db.models.constants import LOOKUP_SEP
from django.template import loader
from rest_framework.filters import BaseFilterBackend
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _


class ContainsFilter(BaseFilterBackend):
    search_param = 'contains'
    template = 'rest_framework/filters/search.html'
    lookup_prefixes = {
        '^': 'istartswith',
        '@': 'search',
        '$': 'iregex',
    }
    search_title = _('Contains')
    search_description = _('A contains term (contains=field:term,another_field:$another_term). Possible filter '
                           'options are ^ (istartswith), @ (search) and $ (iregex).')

    def construct_search(self, field_name):
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            lookup = 'icontains'
        return LOOKUP_SEP.join([field_name, lookup])

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_contains_fields(view)
        try:
            search_terms = self.get_contains_terms(request)
        except ValueError:
            return queryset

        if not search_fields or not search_terms:
            return queryset

        q = queryset

        for search_term in search_terms:
            a, b = search_term.split(':')
            if a not in search_fields:
                continue
            q = q.filter(**{self.construct_search(a): b})

        return q

    def get_contains_fields(self, view):
        return getattr(view, 'contains_fields', None)

    def get_contains_terms(self, request):
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')  # strip null characters
        params = params.split(',')
        for e in params:
            if ':' not in e or len(e.split(':')) != 2:
                raise ValueError()
        return params

    def to_html(self, request, queryset, view):
        if not getattr(view, 'search_fields', None):
            return ''

        term = self.get_contains_terms(request)
        term = term[0] if term else ''
        context = {
            'param': self.search_param,
            'term': term
        }
        template = loader.get_template(self.template)
        return template.render(context)

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.search_param,
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_str(self.search_title),
                    description=force_str(self.search_description + ' Fields that are searchable with contains are: {}'.
                                          format(', '.join(self.get_contains_fields(view))))
                )
            )
        ]

    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.search_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.search_description),
                'schema': {
                    'type': 'string',
                },
            },
        ]


class ListContainsFilter(BaseFilterBackend):
    search_param = 'list_contains'
    template = 'rest_framework/filters/search.html'
    search_title = _('Contains')
    search_description = _('A contains term (list_contains=field:term,another_field:another_term).')

    def filter_queryset(self, request, queryset, view):
        search_fields = self.get_contains_fields(view)
        try:
            search_terms = self.get_contains_terms(request)
        except ValueError:
            return queryset

        if not search_fields or not search_terms:
            return queryset

        q = queryset

        for search_term in search_terms:
            a, b = search_term.split(':')
            if a not in search_fields:
                continue
            q = q.filter(**{LOOKUP_SEP.join([a, 'regex']): "({}$|{},)".format(b, b)})

        return q

    def get_contains_fields(self, view):
        return getattr(view, 'list_contains_fields', None)

    def get_contains_terms(self, request):
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')  # strip null characters
        params = params.split(',')
        for e in params:
            if ':' not in e or len(e.split(':')) != 2:
                raise ValueError()
        return params

    def to_html(self, request, queryset, view):
        if not getattr(view, 'search_fields', None):
            return ''

        term = self.get_contains_terms(request)
        term = term[0] if term else ''
        context = {
            'param': self.search_param,
            'term': term
        }
        template = loader.get_template(self.template)
        return template.render(context)

    def get_schema_fields(self, view):
        assert coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'
        return [
            coreapi.Field(
                name=self.search_param,
                required=False,
                location='query',
                schema=coreschema.String(
                    title=force_str(self.search_title),
                    description=force_str(self.search_description + ' Fields that are searchable with contains are: {}'.
                                          format(', '.join(self.get_contains_fields(view))))
                )
            )
        ]

    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.search_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.search_description),
                'schema': {
                    'type': 'string',
                },
            },
        ]

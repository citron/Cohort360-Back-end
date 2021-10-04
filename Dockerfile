FROM {{IMAGE_REPOSITORY_URL}}/python:{{ENVIR}}
WORKDIR /app
COPY ./ ./
RUN mkdir -p /etc/nginx && mkdir -p /etc/nginx/sites-enabled/
COPY nginx.conf /etc/nginx/sites-enabled/
RUN pip install {{PIP_EXTRA_CLI_PARAMETERS}} -r requirements.txt
# ENV no_proxy=localhost,127.0.0.1,{{ENVIRONMENT}}-fhir-nginx
CMD ["bash", "entry-point.sh"]
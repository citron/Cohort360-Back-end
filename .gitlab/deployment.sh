#!/usr/bin/bash

touch $CI_PROJECT_DIR/cohort_back/.env
# login to docker image repo
echo "{\"auths\":{\"$IMAGE_REGISTRY\":{\"username\":\"$BOT_NAME\",\"password\":\"$BOT_TOKEN\"}}}" > /kaniko/.docker/config.json

# replace env var in Dockerfile
export ENVIR=$(echo $CI_COMMIT_BRANCH)
export ENVIRONMENT=${CI_COMMIT_BRANCH/_/-}
echo $PIP_EXTRA_CLI_PARAMETERS
# for all env var in ENV_VAR_LIST, replace in dockerfile
ENV_VAR_LIST="PIP_EXTRA_CLI_PARAMETERS;IMAGE_REPOSITORY_URL;ENVIRONMENT;ENVIR"
for NAME in `echo $ENV_VAR_LIST | grep -o -e "[^;]*"`; do
  ENV_VAR=$(printenv | grep -E '\b'$NAME'\b' | cut -d '=' -f 2-)
  ENV_VAR=$(echo $ENV_VAR | sed "s/[^a-zA-Z0-9]/\\\\&/g");
  sed -i s/"{{"$NAME"}}"/$ENV_VAR/g Dockerfile;
done

# build and push image on the docker image repo
/kaniko/executor --context $CI_PROJECT_DIR --dockerfile $CI_PROJECT_DIR/Dockerfile --destination $IMAGE_REPOSITORY_URL/back:$CI_COMMIT_BRANCH
FROM python:3.7-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HOME /usr/src/app
ENV GIT_DATA /var/git
ENV GIT_HOST /srv/git
ENV TERRAFORM_DIR /var/terraform

WORKDIR $HOME
RUN adduser --disabled-password python && chown -R python:python $HOME 

RUN mkdir $GIT_DATA && chown -R python:python $GIT_DATA \
 && mkdir $GIT_HOST && chown -R python:python $GIT_HOST \
 && mkdir $TERRAFORM_DIR && chown -R python:python $TERRAFORM_DIR

RUN apk add --no-cache git
COPY --chown=python requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=python . .

USER python


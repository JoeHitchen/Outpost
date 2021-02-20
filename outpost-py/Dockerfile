FROM python:3.7-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HOME /usr/src/app

WORKDIR $HOME
RUN adduser --disabled-password python && chown -R python:python $HOME 

COPY --chown=python requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=python . .

USER python

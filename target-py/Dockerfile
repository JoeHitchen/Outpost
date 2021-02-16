FROM python:3.7-alpine

ARG IMAGE_NAME=mock:0.0.2
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HOME /usr/src/app

WORKDIR $HOME
RUN adduser --disabled-password python && chown -R python:python $HOME

COPY --chown=python . .

RUN sed -i 's/a container/'$IMAGE_NAME'/g' index.html

CMD ["python", "-m", "http.server"]


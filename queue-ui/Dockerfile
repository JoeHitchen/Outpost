FROM python:3.8-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV HOME /usr/src/app

WORKDIR $HOME
RUN adduser --disabled-password python && chown -R python:python $HOME \
 && mkdir /var/dashboard && chown -R python:python /var/dashboard

COPY --chown=python requirements.txt .
RUN pip install -r requirements.txt

USER python
ENTRYPOINT ["flower", "--port=5555"]
EXPOSE 5555


FROM tiangolo/uwsgi-nginx-flask:python3.8
ENV STATIC_URL /static
ENV STATIC_PATH /var/www/3dbag-api/static
COPY ./requirements.txt /var/www/requirements.txt
RUN pip install -r /var/www/requirements.txt
COPY ./.pg_service.conf /etc/.pg_service.conf 
ENV PGSYSCONFDIR /etc
ENV PGSERVICEFILE /etc/.pg_service.conf

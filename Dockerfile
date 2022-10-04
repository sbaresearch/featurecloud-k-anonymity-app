FROM python:3.8-buster

RUN apt-get update && apt-get install -y supervisor nginx && apt-get install -y openjdk-11-jre-headless

RUN pip3 install --upgrade pip

COPY server_config/supervisord.conf /supervisord.conf
COPY server_config/nginx /etc/nginx/sites-available/default
COPY server_config/docker-entrypoint.sh /entrypoint.sh
COPY executable/libarx-3.9.0.jar /libarx-3.9.0.jar

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r ./app/requirements.txt

COPY . /app

EXPOSE 9000 9001

ENTRYPOINT ["sh", "/entrypoint.sh"]

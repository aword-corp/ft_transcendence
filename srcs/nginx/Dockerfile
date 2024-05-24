FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
	curl \
	gnupg2 \
	ca-certificates \
	lsb-release \
	debian-archive-keyring

RUN curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor \
	| tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null

RUN echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
	http://nginx.org/packages/debian $(lsb_release -cs) nginx" \
	| tee /etc/apt/sources.list.d/nginx.list

RUN apt-get update && apt-get install -y \
	openssl \
	nginx

COPY conf/nginx.conf /etc/nginx/

COPY conf/mime.types /etc/nginx/conf/

COPY conf/a-corp.ninja.conf /etc/nginx/sites-enabled/

COPY conf/a-corp.ninja.crt /etc/ssl/certs/

COPY conf/a-corp.ninja.key /etc/ssl/private/

COPY conf/acorp.games.conf /etc/nginx/sites-enabled/

COPY conf/acorp.games.crt /etc/ssl/certs/

COPY conf/acorp.games.key /etc/ssl/private/

COPY conf/localhost.conf /etc/nginx/sites-enabled/

COPY conf/localhost.crt /etc/ssl/certs/

COPY conf/localhost.key /etc/ssl/private/

ADD conf/front/ /var/www/front/

RUN chown -R www-data:www-data /var/www/front

RUN chmod -R 755 /var/www/front

EXPOSE 443 443/udp

ENTRYPOINT ["nginx", "-g", "daemon off;"]

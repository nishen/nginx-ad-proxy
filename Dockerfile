FROM python:3.12.3-slim

WORKDIR /opt/service-auth-ad

# If your AD doesn't support newer TLS protocols, this line helps.
# Uncomment if you have issues.
#RUN sed -i 's/MinProtocol = TLSv1.2/MinProtocol = TLSv1/' /etc/ssl/openssl.cnf \
#&& sed -i 's/CipherString = DEFAULT@SECLEVEL=2/CipherString = DEFAULT@SECLEVEL=1/' /etc/ssl/openssl.cnf

ADD Pipfile ./
ADD active_directory_dao.py ./
ADD nginx_ad_proxy.py ./

RUN pip install pipenv && pipenv install

CMD ["pipenv", "run", "launch"]

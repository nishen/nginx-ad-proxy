FROM python:3.8-slim

WORKDIR /opt/service-auth-ad

ADD * ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:80", "service_auth_ad:api"]

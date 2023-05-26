FROM python:3.8-slim

WORKDIR /opt/service-auth-ad

ADD * ./

RUN pip install pipenv && pipenv install

CMD ["pipenv", "run", "launch"]

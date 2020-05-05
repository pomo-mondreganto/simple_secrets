FROM python:3.7

COPY src/requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

COPY src /app

COPY ./config/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
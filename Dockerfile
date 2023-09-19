FROM python:3.11

WORKDIR /opt/app
COPY src/requirements.txt .
RUN pip3 install -r requirements.txt

ADD src/rollershutter.py .
ADD src/health_check.py .

ENV MQTT_HOST t20
ENV MQTT_PORT 1883
ENV FHEM_HOST minicul-raspi
ENV FHEM_PORT 8083
ENV TIME_OPEN 53
ENV TIME_CLOSE 53 
ENV ROLLERSHUTTER_NAME Test1

HEALTHCHECK CMD ["python", "health_check.py"]
CMD ["python", "rollershutter.py"]
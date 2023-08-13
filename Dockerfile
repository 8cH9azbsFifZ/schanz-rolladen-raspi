FROM python:3.11

WORKDIR /opt/app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ADD rollershutter.py .

ENV MQTT_HOST
ENV MQTT_PORT
ENV FHEM_HOST
ENV FHEM_PORT
ENV TIME_OPEN
ENV TIME_CLOSE
ENV ROLLERSHUTTER_NAME
ENV SIMULATION

CMD ["python", "rollershutter.py"]
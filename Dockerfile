FROM python:3.11

WORKDIR /opt/app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ADD rollershutter.py .

CMD ["python", "rollershutter.py"]


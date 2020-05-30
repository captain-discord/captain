FROM python:latest

COPY . /opt/bot

WORKDIR /opt/bot

RUN python3.8 -m pip install -r requirements.txt

WORKDIR /opt/bot/artemis

CMD ["python3.8", "bot.py"]
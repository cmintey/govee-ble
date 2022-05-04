# FROM debian:stable-slim
FROM python:3-slim

RUN apt update && apt install -y bluez bluetooth bluez-tools rfkill
RUN pip3 install bleak pyyaml paho-mqtt

ENTRYPOINT ["python3", "/src/main.py"]

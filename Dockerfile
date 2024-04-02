FROM python:3.8.3-slim-buster

LABEL "maintainer"="xiehuan <1208044257@qq.com>"
LABEL "repository"="https://github.com/xiehuan123/xiehuan-ssh"
LABEL "version"="v1.1.0"

LABEL "com.github.actions.name"="xiehuan-ssh"
LABEL "com.github.actions.description"="Pipeline: scp"
LABEL "com.github.actions.icon"="copy"
LABEL "com.github.actions.color"="gray-dark"

RUN apt-get update -y && \
  apt-get install -y ca-certificates openssh-client openssl sshpass

COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

RUN mkdir -p /opt/tools

COPY entrypoint.sh /opt/tools/entrypoint.sh
RUN chmod +x /opt/tools/entrypoint.sh

COPY app.py /opt/tools/app.py
RUN chmod +x /opt/tools/app.py

ENTRYPOINT ["/opt/tools/entrypoint.sh"]
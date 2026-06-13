FROM ubuntu:latest
LABEL authors="tesreq"

ENTRYPOINT ["top", "-b"]
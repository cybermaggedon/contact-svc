
FROM python:3.12.2-alpine3.19 AS build

env PACKAGE_VERSION=0.0.0

RUN pip3 install wheel

RUN mkdir /root/wheels

COPY contact /root/build/contact
COPY scripts /root/build/scripts
COPY setup.py /root/build/
COPY README.md /root/build/

RUN (cd /root/build && pip3 wheel -w /root/wheels --no-deps . )

FROM python:3.12.2-alpine3.19

COPY --from=build /root/wheels /root/wheels

RUN pip3 --no-cache-dir install /root/wheels/* && \
    rm -rf /root/wheels

RUN mkdir /data
COPY questions.json /data/
WORKDIR /data

CMD /usr/local/bin/contact-svc -q
EXPOSE 8080


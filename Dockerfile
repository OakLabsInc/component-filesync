FROM oaklabs/grpcio-tools:python3.7.0-1.15.0 as protos

COPY filesync.proto /protos/

RUN python -m grpc_tools.protoc --proto_path=/protos/ --python_out=/protos/ --grpc_python_out=/protos/ /protos/*.proto


FROM python:2.7.15-alpine3.8
# Using google/cloud-sdk:218.0.0-alpine will lead to a BIGGER image

# See https://hub.docker.com/r/camil/gsutil/~/dockerfile/
RUN apk add --no-cache \
    bash=4.4.19-r1 \
    coreutils=8.29-r2 \
    g++=6.4.0-r9 \
    gcc=6.4.0-r9 \
    gettext=0.19.8.1-r2 \
    libffi-dev=3.2.1-r4  \
    linux-headers \
    musl-dev \
    nginx=1.14.2-r0 \
    openssl-dev \
    py-cffi \
    py-cryptography \
    python2-dev=2.7.15-r1 \
    supervisor=3.3.4-r1 \
    && pip install gsutil \
    && rm -rf /var/cache/apk/*

RUN rm -f /etc/nginx/conf.d/*

WORKDIR /src

COPY filesync/requirements.txt ./filesync/

RUN pip install -r ./filesync/requirements.txt

COPY filesync ./filesync
COPY bin ./bin
COPY conf /conf

COPY --from=protos /protos/ /protos/

ENV BOTO_CONFIG=/conf/boto-config.conf \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/protos/ \
    CONTROL_PORT=9102 \
    DATA_PORT=9103

CMD /usr/bin/supervisord -c /conf/supervisor.conf

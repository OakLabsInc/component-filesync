# Filesync - Google Cloud Storage Syncing

[![Dockerhub](https://img.shields.io/static/v1.svg?label=Docker%20Hub&message=latest&color=green)](https://hub.docker.com/r/oaklabs/component-filesync)

This service will periodically, atomically sync a Google Cloud Storage
directory to this container and server the contents over http.

Requirements for use:

* `CONTROL_PORT` env var - port that the control gRPC interface listens on.  {DEFAULT: 9102}
* `DATA_PORT` env var - port that the files are served on {DEFAULT: 9103}
* `GS_URL` env var - gs:// url to the Google Cloud Storage directory where the
  files are downloaded from
* `SYNC_DIR` env var - absolute path to the directory in the container the files
  should be stored it; this should be a persistent volume and will
  need to have at least 2x the amount of space that the GCS directory
  uses
* `SYNC_PERIOD` env var - how often in seconds syncing should begin; if syncing
  is ongoing then the period just restarts
* GCP service account credentails mounted at `/gcloud-credentials.json`

This service can be signaled to wait before downloading by placing an
empty file called `WAIT` in the top of the SYNC_DIR:

```
# Turn waiting on
gsutil cp /dev/null gs://path/to/sync_dir/WAIT

# Turn waiting off
gsutil rm gs://path/to/sync_dir/WAIT
```

# Dev Notes

The script `tryit.py` can be used to test the control interface. You
can use `curl` to view the files. Here's a quick way to test the whole
flow:

```
echo 'GS_URL=gs://your/gcs/directory/' > .env

pip install grpcio grpcio-tools

python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. *.proto

docker-compose up --build -d

python tryit.py localhost:9102

curl http://localhost:9103/
```

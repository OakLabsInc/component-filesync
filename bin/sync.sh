#!/bin/bash

GS_URL="$1"
WAIT_INTERVAL_SECONDS=10

swap_idle_and_live () {
    # Moving a symlink is not an atomic operation.
    # Instead, we do this dance.
    # See http://blog.moertel.com/posts/2005-08-22-how-to-change-symlinks-atomically.html
    cp -P live tmp
    mv -Tf idle live
    mv -Tf tmp idle
}

echo "=== Verifying credentials"

if ! (gsutil ls "$GS_URL" >/dev/null 2>/dev/null); then
    echo "Credentials are invalid. Make sure /gcloud-credentials.json is present and grants read access to $GS_URL"
    exit 1
fi

echo "=== Checking for WAIT file"
while gsutil -q stat "$GS_URL/WAIT"; do
    echo "=== $GS_URL/WAIT exists. Waiting until it's gone..."
    sleep $WAIT_INTERVAL_SECONDS
done

echo "=== Downloading $GS_URL"
gsutil $GSUTIL_OPT -m rsync -d -r "$GS_URL" idle/
echo "=== Download complete, making it live"
swap_idle_and_live
echo "=== Copying live back to idle"
gsutil $GSUTIL_OPT rsync -d -r live/ idle/

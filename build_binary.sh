#!/bin/bash

IMAGE_ID=$(docker build --pull --quiet --file Dockerfile.builder .)
CONTAINER_ID=$(docker create $IMAGE_ID)
docker cp $CONTAINER_ID:/app/wtf-ds-static wtf-ds

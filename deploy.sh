#!/bin/bash

docker stop manguling
docker rm manguling
rm -r build

mkdir build
mkdir build/app

cp run.py build/.
cp requirements.txt build/.
cp Dockerfile build/.
cp -r app/* build/app/.

docker build -t manguling build/.
docker run -t -d -p 8001:5000 --env-file .env --network orangesip --privileged --name manguling manguling
docker ps -a
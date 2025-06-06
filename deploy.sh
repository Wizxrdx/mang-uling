#!/bin/bash

docker stop manguling
docker rm manguling
rm -r build

mkdir build
mkdir build/app
mkdir build/forecasting
mkdir build/migrations

cp run.py build/.
cp requirements.txt build/.
cp Dockerfile build/.
cp -r app/* build/app/.
cp -r forecasting/* build/forecasting/.
cp -r migrations/* build/migrations/.

docker build -t manguling build/.
docker run -t -d -p 8001:5000 --privileged --name manguling manguling
docker ps -a
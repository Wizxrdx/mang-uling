#!/bin/bash

docker stop manguling
docker rm manguling
rm -r build

mkdir build
mkdir build/app
mkdir build/forecasting

cp run.py build/.
cp requirements.txt build/.
cp Dockerfile build/.
cp populate_data.py build/.
cp -r app/* build/app/.
cp -r forecasting/* build/forecasting/.

docker build -t manguling build/.
docker run -t -d -p 8001:5000 --privileged --name manguling manguling
docker ps -a
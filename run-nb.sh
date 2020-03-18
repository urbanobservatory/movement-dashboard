#!/bin/bash

docker run --rm -p 8888:8888 --user root -e JUPYTER_ENABLE_LAB=yes -e GRANT_SUDO=yes -v "/$PWD":/home/jovyan/movement-dashboard jupyter/datascience-notebook


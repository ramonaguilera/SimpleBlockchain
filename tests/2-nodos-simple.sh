#!/bin/sh
screen -S minero1 -dm bash -c 'cd ..;python3 minero.py -d 5 -m 1-2 -i 100 -log -parar'
screen -S minero2 -dm bash -c 'cd ..;python3 minero.py -d 5 -m 2-2 -i 100 -parar' 
#!/bin/sh
screen -S minero1 -dm bash -c 'cd ..;python3 minero.py -d 5 -m 1-5 -i 100 -log -parar'
screen -S minero2 -dm bash -c 'cd ..;python3 minero.py -d 5 -m 2-5 -i 100 -parar' 
screen -S minero3 -dm bash -c 'cd ..;python3 minero.py -d 5 -m 3-5 -i 100 -parar'
screen -S minero4 -dm bash -c 'cd ..;python3 minero.py -d 5 -m 4-5 -i 100 -parar'  
screen -S minero5 -dm bash -c 'cd ..;python3 minero.py -d 5 -m 5-5 -i 100 -parar'
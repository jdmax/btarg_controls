#!/usr/bin/bash

screen -X -S manager quit
screen -S manager bash -c "/home/poltar/btarg_controls/setup.sh"

#!/bin/bash

pkill -f ioc_manager.py
source "venv/bin/activate"
python ioc_manager.py
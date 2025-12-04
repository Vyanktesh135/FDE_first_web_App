#!/bin/bash
set -e

#backend
pip install -r requirements.txt
alembic upgrade head
python converter.py

# #frontend
cd frontend
npm install
npm run build
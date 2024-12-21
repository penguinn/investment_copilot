#!/bin/bash

# 启动后端服务
cd backend
source venv/bin/activate
python manage.py runserver &

# 启动前端服务
cd ../frontend
yarn start 
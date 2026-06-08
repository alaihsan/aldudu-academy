#!/bin/bash

# Aldudu Academy - Robust Server Reset Script
# Automates the restart of Gunicorn (Web) and Celery (Workers)

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Memulai Reset Server Aldudu Academy...${NC}"

# 1. Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ ERROR: File .env tidak ditemukan!${NC}"
    echo -e "${YELLOW}Silakan buat file .env atau rename '.env copy.example' menjadi '.env'${NC}"
    exit 1
fi

# 2. Kill existing processes
echo -e "${RED}🛑 Mematikan proses Gunicorn dan Celery lama...${NC}"
pkill -f gunicorn
pkill -f celery
sleep 2

# 3. Force clear port 5055
PORT_PID=$(lsof -t -i:5055)
if [ ! -z "$PORT_PID" ]; then
    echo -e "${RED}⚠️ Port 5055 masih terpakai oleh PID $PORT_PID. Mematikan paksa...${NC}"
    kill -9 $PORT_PID
    sleep 1
fi

# 4. Start Gunicorn (Web Server)
echo -e "${GREEN}🌐 Menghidupkan Gunicorn (Web Server) pada port 5055...${NC}"
if [ -f "venv/bin/gunicorn" ]; then
    venv/bin/gunicorn -w 4 -b 0.0.0.0:5055 run:app --daemon --access-logfile gunicorn_access.log --error-logfile gunicorn_error.log
else
    gunicorn -w 4 -b 0.0.0.0:5055 run:app --daemon --access-logfile gunicorn_access.log --error-logfile gunicorn_error.log
fi

# 5. Start Celery Worker
echo -e "${GREEN}⚙️ Menghidupkan Celery Worker...${NC}"
if [ -f "venv/bin/python" ]; then
    nohup venv/bin/python run_worker.py > celery.log 2>&1 &
else
    nohup python3 run_worker.py > celery.log 2>&1 &
fi

echo -e "\n${BLUE}=======================================${NC}"
echo -e "${GREEN}✅ SERVER BERHASIL DIHIDUPKAN!${NC}"
echo -e "📍 Web App  : http://localhost:5055"
echo -e "📍 Log Error: tail -f gunicorn_error.log"
echo -e "📍 Log Task : tail -f celery.log"
echo -e "${BLUE}=======================================${NC}"

#! /bin/sh

echo "Running app..."
if [ -d ".env" ];
then
    echo "Enabling virtual environment..."
else
    echo "No virtual environment found. Please run local_setup.sh first"
    exit N
fi

. .env/bin/activate
export ENV=development
python3 run.py
deactivate

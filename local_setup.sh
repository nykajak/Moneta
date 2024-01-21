#! /bin/sh

echo "Setting up app..."

if [ -d "instance" ];
then
    echo "Database directory already exists."
else
    echo "Creating database directory..."
    mkdir instance
fi

if [ -d ".env" ];
then
    echo "Virtual environment already exists."
else
    echo "Creating virtual environment..."
    python3 -m venv .env
fi

echo "Installing dependecies..."

. .env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

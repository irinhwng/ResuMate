#!/bin/bash


# global vars
VENV_NAME="resumate-env"
PYTHON_VERSION="3.12.1"
REQUIREMENTS_FILE="requirements.txt"

# Load environment variables from .env file
if [ -f .env ]; then
    source .env
else
    echo ".env file not found. Exiting."
    exit 1
fi

# Check for DS API KEY
if [ -z "$DEEPSEARCH_API_KEY" ]; then
    echo "DEEPSEARCH_API_KEY is not set. Exiting."
    exit 1
fi

# Ensure pyenv is initialized
if ! command -v pyenv &> /dev/null; then
    echo "pyenv is not installed or not in PATH. Please install pyenv first."
    exit 1
fi

#update shims to recognie new binaries when another version of python is installed
pyenv rehash

# Check if the virtualenv exists
if pyenv virtualenvs | grep -q "$VENV_NAME"; then
    echo "Virtual environment '$VENV_NAME' already exists."
else
    echo "Virtual environment '$VENV_NAME' does not exist. Checking for Python $PYTHON_VERSION..."

    # Ensure Python 3.12.1 is installed
    if ! pyenv versions | grep -q "$PYTHON_VERSION"; then
        echo "Python $PYTHON_VERSION is not installed. Installing..."
        pyenv install $PYTHON_VERSION
    else
        echo "Python $PYTHON_VERSION is already installed."
    fi

    # Create the virtual environment
    echo "Creating virtual environment '$VENV_NAME' with Python $PYTHON_VERSION..."
    pyenv virtualenv $PYTHON_VERSION $VENV_NAME
    echo "Virtual environment '$VENV_NAME' has been created successfully."
fi

# Activate the virtual environment
echo "Activating virtual environment '$VENV_NAME'..."
pyenv activate $VENV_NAME

# Check if requirements.txt exists and install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    echo "Dependencies installed successfully."

    echo "Configuring DeepSearch profile..."
    if deepsearch profile config --profile-name "ds-experience" \
        --host "https://deepsearch-experience.res.ibm.com/" \
        --no-verify-ssl \
        --username "hwangeee123@gmail.com" \
        --api-key "$DEEPSEARCH_API_KEY"; then
        echo "DeepSearch profile configured successfully."
    else
        echo "Failed to configure DeepSearch profile."
        exit 1
    fi
else
    echo "No $REQUIREMENTS_FILE found. Skipping dependency installation."
fi
pyenv deactivate

# Provide instructions for activating the virtual environment
echo "To activate the virtual environment, use: pyenv activate $VENV_NAME"

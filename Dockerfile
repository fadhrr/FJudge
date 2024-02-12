# Use bookworm distro
FROM python:3.11-slim

# Set the working directory
WORKDIR /code

# Copy requirements.txt to the working directory
COPY ./requirements.txt /code/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Set up environment for C++ and Java
RUN apt-get update && apt-get install -y default-jdk g++

# Copy the application code and static files
COPY ./app /code/app
COPY ./static /code/static
COPY ./templates /code/templates

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]

# 
FROM python:3.11-alpine

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Set up environment for C++ and Java
RUN apk update && apk add openjdk11 g++

# 
COPY ./app /code/app
COPY ./static /code/static
COPY ./templates /code/templates

# Use an official lightweight Python image.
FROM python:3.8-slim-bullseye

# Set the working directory in docker
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
# COPY app.py .
COPY hello.py .
ADD pages pages

# Specify the command to run on container start
CMD ["streamlit", "run", "hello.py"]

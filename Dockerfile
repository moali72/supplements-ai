FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install Tesseract and other dependencies
RUN apt-get update && apt-get install -y tesseract-ocr  libtesseract-dev && apt-get clean

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Command to run your application
CMD ["python", "app.py"]
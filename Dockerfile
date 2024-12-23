FROM python:3.11-bullseye

# Set environment variable
ENV PYTHONBUFFERED=1

# Set the working directory to the main project folder
WORKDIR /test_backend

# Copy the requirements file and install dependencies
COPY requirements.txt /test_backend/
RUN pip3 install -r requirements.txt

# Copy the rest of the application code
COPY . /test_backend/

# Set the working directory to the backend folder where manage.py is located
WORKDIR /test_backend/backend

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


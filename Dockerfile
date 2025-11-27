# Use Python 3.11 based on Debian Bullseye (compatible with MS ODBC driver)
FROM python:3.11-bullseye

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files and enable stdout/stderr immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for pyodbc and SQL Server driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    apt-transport-https \
    unixodbc-dev \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository and install ODBC Driver 18
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files explicitly
# COPY app.py .
# COPY db_connection.py .
# COPY login_logout.py .
# COPY user_interface.py .
# COPY embed_token_url.py .
# COPY admin_users.py .
# COPY admin_reports.py .
# COPY admin_permissions.py .
# COPY admin_overview.py .
# COPY admin_departments.py .
# COPY admin_configuration_test.py .
# COPY .env .
COPY . .

# If you have templates or static folders, copy them
# COPY templates/ ./templates/
# COPY static/ ./static/

# Expose Flask port
EXPOSE 5000

# Command to run Flask app via Gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
# CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:80", "app:app"]


CMD ["python","app.py"]

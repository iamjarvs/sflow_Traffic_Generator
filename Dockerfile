FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Add initial apt configuration and install basic dependencies
RUN apt-get update && \
    apt-get install -y \
        software-properties-common \
        gnupg \
        curl \
        apt-transport-https \
        python3 \
        python3-pip \
        python3-dev \
        supervisor \
        build-essential \
        libssl-dev \
        libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Ansible via pip instead of apt
RUN pip3 install ansible
RUN pip3 install "streamlit>=1.28.0"

# Create non-root user
RUN useradd -m -s /bin/bash appuser

# Create necessary directories
RUN mkdir -p /app/src/ansible/playbooks \
    && mkdir -p /app/src/ansible/vars \
    && mkdir -p /app/src/UI \
    && mkdir -p /app/src/flaskAPI \
    && mkdir -p /app/src/config \
    && mkdir -p /app/src/scripts \
    && mkdir -p /var/log/supervisor

# Set up log files and permissions
RUN touch /var/log/ui.err.log /var/log/ui.out.log \
    /var/log/api.err.log /var/log/api.out.log \
    && chown -R appuser:appuser /app /var/log/ui.* /var/log/api.*

# Copy project files from your development directory to the container
COPY requirements.txt /app/

# Copy the entire src directory with all its contents
COPY src/UI/ui.py /app/src/UI/
COPY src/flaskAPI/api.py /app/src/flaskAPI/
COPY src/ansible/inventory.ini /app/src/ansible/
COPY src/ansible/playbooks/ /app/src/ansible/playbooks/
COPY src/ansible/vars/ /app/src/ansible/vars/
COPY src/scripts/ /app/src/scripts/
COPY src/config/ /app/src/config/

# Set ownership of copied files
RUN chown -R appuser:appuser /app \
    && chmod -R 755 /app

# Install Python dependencies
WORKDIR /app
RUN pip3 install -r requirements.txt

# Create Streamlit config directory and copy config
RUN mkdir -p /home/appuser/.streamlit
COPY src/config/streamlit/config.toml /home/appuser/.streamlit/
RUN chown -R appuser:appuser /home/appuser/.streamlit

# Copy supervisor configuration
COPY src/config/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set the working directory
WORKDIR /app

# Start supervisord directly
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
FROM python:3.11-slim

WORKDIR /app

# Install packet sniffing dependencies (libpcap-dev for Linux)
RUN apt-get update && apt-get install -y libpcap-dev iw net-tools iproute2 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# In docker, the agent needs to be run with --network host and --privileged to sniff correctly
CMD ["python", "main.py"]

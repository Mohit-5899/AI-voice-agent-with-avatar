FROM python:3.12-slim

# Install system libraries required by LiveKit's native FFI bindings
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgobject-2.0-0 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libsrtp2-1 \
    libnice10 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download plugin model files (turn-detector ONNX, etc.) at startup,
# then start the agent. download-files needs network + HF Hub access.
CMD ["sh", "-c", "python agent.py download-files && python agent.py start"]

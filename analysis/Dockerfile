From python:3.13-slim

WORKDIR /app

# Install Dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Expose Port for fastapi
EXPOSE 8000

# Run the fastapi server via uvicorn
CMD ['uvicorn','main:app', '--host', '0.0.0.0', '--port', '8000', '--reload']

# Stage 1: Build the React frontend
FROM node:18-alpine AS build

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

# Copy the rest of the frontend source code
COPY frontend/ ./

# Build the React application
RUN npm run build

# Stage 2: Build the Python backend
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code
COPY . .

# Copy the built frontend from the build stage
COPY --from=build /app/frontend/dist ./frontend/dist

# Set permissions
RUN chmod +x /app/entrypoint.sh
RUN useradd -ms /bin/bash odinuser && chown -R odinuser:odinuser /app
USER odinuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "main.py"]
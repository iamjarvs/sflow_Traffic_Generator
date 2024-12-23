#!/bin/bash

# Configuration
IMAGE_NAME="ansible-ui"
CONTAINER_NAME="ansible-ui-container"

echo "🔄 Starting deployment process..."

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "🛑 Stopping existing container..."
    docker stop $CONTAINER_NAME
    echo "🗑️ Removing existing container..."
    docker rm $CONTAINER_NAME
fi

# Remove old image
if [ "$(docker images -q $IMAGE_NAME)" ]; then
    echo "🗑️ Removing old image..."
    docker rmi $IMAGE_NAME
fi

# Build new image
echo "🏗️ Building new image..."
docker build -t $IMAGE_NAME .

# Run new container
echo "🚀 Starting new container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p 8501:8501 \
    -p 5001:5000 \
    $IMAGE_NAME

# Check if container is running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "✅ Container successfully started!"
    echo "💻 UI available at http://localhost:8501"
    echo "🔌 API available at http://localhost:5001"
    echo "📝 Starting log stream (Press Ctrl+C to exit)..."
    echo "----------------------------------------"
    # Show the logs from both the supervisor and the applications
    docker exec $CONTAINER_NAME tail -f /var/log/supervisord.log /var/log/ui.err.log /var/log/api.err.log
else
    echo "❌ Container failed to start!"
    exit 1
fi

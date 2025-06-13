FROM node:18-alpine

WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Create necessary directories
RUN mkdir -p data logs public

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Start the application
CMD ["node", "server.js"]
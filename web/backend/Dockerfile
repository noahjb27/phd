# Use an official Node runtime as a parent image
FROM node:16

# Set the workin directory of the container
WORKDIR /usr/src/app

# Copy package.json
COPY package*.json ./

# Install the backend dependencies
RUN npm install

# copy the backend app code
COPY . .

# Expose the app ports
EXPOSE 5000

# Start the backend server

CMD ["npm", "start"]
# Use an official Nginx runtime as a parent image
FROM nginx:alpine

# Copy the nginx configuration template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# When the container starts, it will substitute environment variables
# in the template and output the final configuration to the correct directory.
CMD ["/bin/sh", "-c", "envsubst '$${PROJECT_PREFIX}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]

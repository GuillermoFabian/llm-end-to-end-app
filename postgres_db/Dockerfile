FROM postgres:14

# Set custom environment variables
ENV POSTGRES_DB=${POSTGRES_DB}
ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Custom PostgreSQL configuration
COPY postgresql.conf /etc/postgresql/postgresql.conf

# Set custom port
EXPOSE 5433

# Use custom configuration file
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
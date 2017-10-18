FROM python:3

# Install required packages and remove the apt packages cache when done.
RUN apt-get update \
    && \
    apt-get upgrade -y \
    && \
    apt-get install -y \
        nginx \
        supervisor \
        libxslt1-dev \
        libxml2-dev \
        libjpeg-dev \
        libgdal-dev \
        libmemcached-dev \
        libffi-dev \
    && \
    pip3 install -U pip setuptools \
    && \
    rm -rf /var/lib/apt/lists/*

# Setup Env
ENV C_INCLUDE_PATH='/usr/include/gdal'
ENV CPLUS_INCLUDE_PATH='/usr/include/gdal'
RUN mkdir -p /var/log/django/

# Setup User
RUN useradd -M -d /opt/cadasta/code user

# COPY requirements.txt and RUN pip install BEFORE adding the rest of your code, this will cause Docker's caching mechanism
# to prevent re-installing (all your) dependencies when you made a change a line or two in your app.
COPY ./requirements /opt/cadasta/requirements
RUN chown -R user.user /opt/cadasta
RUN chown -R user.user /var/log/django
RUN pip3 install -r /opt/cadasta/requirements/dev.txt

# add (the rest of) our code
COPY --chown=user:user ./cadasta /opt/cadasta/code

USER user
WORKDIR /opt/cadasta/code
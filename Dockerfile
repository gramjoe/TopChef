# Dockerfile to set up the TopChef server, exposing port 80 in the container

# Start with the latest minimum debian distribution
FROM debian:latest

# Define API metadata
MAINTAINER Michal Kononenko "@MichalKononenko"

ENV VERSION "1.0-rc1"
ENV DESCRIPTION "Asynchronous job queue for running services"

ENV SOURCE_REPOSITORY "https://github.com/TopChef/TopChef.git" 

ENV HOSTNAME "0.0.0.0"
ENV PORT "80"
ENV THREADS "20"
ENV DEBUG "TRUE"


ENV BASE_DIRECTORY "/var/www/topchef"
ENV SCHEMA_DIRECTORY "/var/www/topchef/schemas"

ENV LOGFILE "/var/www/topchef/topchef.log"

ENV DATABASE_URI "sqlite:////var/www/topchef/db.sqlite3"

# Download the Debian dependencies for installing the
# topchef package.
RUN apt-get update
RUN apt-get -y upgrade

RUN apt-get install -y apt-utils \
    apache2 \
    libapache2-mod-wsgi \
    python \
    python-dev \
    python-pip \
    git \
    wget \
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists

# Copy this package's code into /opt. After running
# setup.py, this package is installed into the site-packages
# directory. At this point, the source code will no longer
# be required.
COPY . /opt/source
WORKDIR /opt/source

RUN pip install -r requirements.txt
RUN python setup.py install

# Copy in the apache configuration file so that Apache is aware of
# topchef's existence. 
COPY ./apache/topchef.conf /etc/apache2/sites-available/topchef.conf

# Copy the WSGI file. The WSGI file imports the flask app as the
# variable ``application``. Apache's mod_wsgi looks for this application
# and then runs it in the context of an apache server
COPY ./apache/topchef.wsgi /var/www/topchef/topchef.wsgi

# Create the sqlite DB to manage relational data. Create a schema directory
# to house all the JSON Schemas that the API will generate.
# Enable the site on apache
RUN python ./apache/create_db.py
WORKDIR /var/www/topchef
RUN mkdir /var/www/topchef/schemas
RUN a2dissite 000-default.conf
RUN a2ensite topchef.conf

# Now that the source repository has been copied, remove the 
# cloned Git repository
RUN rm -r /opt/source

# Remove the extensions used to install topchef
RUN apt-get remove -y --purge python-dev \
    python-pip \
    git \
 && apt-get clean \
 && apt-get autoremove -y

# Due to a bug in the apt package system, removal of python-pip
# breaks pkg_resources. This means Debian is no longer able to
# read third-party packages. The wget here reinstalls setuptools
# as a workaround to the bug. This saves 200 MB of disk space
# on the container
RUN wget https://bootstrap.pypa.io/ez_setup.py -O - | python

# Wget is no longer necessary, remove it
RUN apt-get remove -y --purge wget \
 && apt-get clean \
 && apt-get autoremove -y

# Allow topchef to write to the schema directory, the DB, and the log
RUN chown root:www-data /var/www/topchef
RUN chmod 775 /var/www/topchef
RUN chown www-data:www-data /var/www/topchef/schemas
RUN chmod 775 /var/www/topchef/schemas
RUN chown root:www-data /var/www/topchef/db.sqlite3
RUN chmod 664 /var/www/topchef/db.sqlite3
RUN chown root:www-data /var/www/topchef/topchef.log
RUN chmod 664 /var/www/topchef/topchef.log

EXPOSE 80

ENTRYPOINT /usr/sbin/apache2ctl -D FOREGROUND


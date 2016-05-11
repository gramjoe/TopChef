"""
Contains user-serviceable configuration parameters
"""
import os

# HOSTING PARAMETERS
PORT = 5000
HOSTNAME = 'localhost'
THREADS = 3
DEBUG = True

#DIRECTORY
BASE_DIRECTORY = os.path.abspath(os.path.curdir)

# DATABASE
DATABASE_URI = 'sqlite://%s/db.sqlite' % BASE_DIRECTORY


# ROOT USER
ROOT_USERNAME = 'root'
ROOT_EMAIL = 'mkononen@uwaterloo.ca'

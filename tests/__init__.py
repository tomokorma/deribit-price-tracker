import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', 'dev.env'))

# Redefining environment variables for tests.
if os.getenv('TESTING_IN_CONTAINER') != '1':
    os.environ['POSTGRES_HOST'] = 'localhost'

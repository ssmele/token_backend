from os import environ
environ['BACKEND_CONFIG'] = '/home/ubuntu/TOKER/backend/configs/config.sample.yml'
from TOKER import app

if __name__ == "__main__":
    app.run(port=8088)

from app import create_app
from app.config import Config

HOST = Config.HOST
PORT = Config.PORT

app = create_app(Config)

if __name__ == '__main__':
    import bjoern

    app.logger.info(f'Running on http://{Config.HOST}:{Config.PORT}')
    bjoern.run(app, host=HOST, port=PORT)

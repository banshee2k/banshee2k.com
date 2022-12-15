import atexit

from app import app as application
from app import DB


def close_db():
    DB.close()


if __name__ == "__main__":
    atexit.register(close_db)
    application.run(debug=True)

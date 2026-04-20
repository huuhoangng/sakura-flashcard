import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secretkey123456abcdef')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///flashcards.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'key123456abcdef')
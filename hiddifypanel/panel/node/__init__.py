from flask import Flask




from . import test_pb2_grpc
from .hello import HelloServicer
def init_app(app:Flask):
    test_pb2_grpc.add_HelloServicer_to_server(HelloServicer(),app.wsgi_app)
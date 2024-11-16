import grpc

# from hiddifypanel.hasync.config import BoolConfig 
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from . import test_pb2
from . import test_pb2_grpc

class HelloServicer(test_pb2_grpc.HelloServicer):
    """Missing associated documentation comment in .proto file."""

    def SayHello(self, request: test_pb2.HelloRequest, context) -> test_pb2.HelloResponse:
            
            return test_pb2.HelloResponse(res=hconfig(ConfigEnum.log_level))

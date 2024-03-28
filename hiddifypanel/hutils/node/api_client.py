from typing import TypeVar, Type, Optional, Union
from apiflask import Schema, fields
import traceback
import requests

from hiddifypanel.models import hconfig, ConfigEnum

T = TypeVar('T', bound=Schema)


class ErrorSchema(Schema):
    msg = fields.String(required=True)
    stacktrace = fields.String(required=True)
    code = fields.Integer(required=True)
    reason = fields.String(required=True)


class NodeApiClient():
    def __init__(self, base_url: str, apikey: Optional[str] = None, max_retry: int = 3):
        self.base_url = base_url
        self.max_retry = max_retry
        self.headers = {'Hiddify-API-Key': apikey if apikey else hconfig(ConfigEnum.unique_id)}

    def __call(self, method: str, path: str, payload: Optional[Schema], output_schema: Type[T]) -> Union[T, ErrorSchema]:  # type: ignore
        retry_count = 1
        full_url = self.base_url + path
        while 1:
            try:
                # TODO: implement it with aiohttp
                if payload:
                    response = requests.request(method, full_url, json=payload.dump(payload), headers=self.headers)
                else:
                    response = requests.request(method, full_url, headers=self.headers)

                response.raise_for_status()
                resp = response.json()
                if not resp:
                    err = ErrorSchema()
                    err.msg = 'Empty response'  # type: ignore
                    err.stacktrace = ''  # type: ignore
                    err.code = response.status_code  # type: ignore
                    err.reason = response.reason  # type: ignore
                    return err
                return resp if isinstance(output_schema, dict) else output_schema().load(resp)
            except requests.HTTPError as e:
                if retry_count >= self.max_retry:
                    stack_trace = traceback.format_exc()
                    err = ErrorSchema()
                    err.msg = str(e)  # type: ignore
                    err.stacktrace = stack_trace  # type: ignore
                    err.code = response.status_code  # type: ignore
                    err.reason = response.reason  # type: ignore
                    return err

                print(f"Error occurred: {e}")
                retry_count += 1

    def get(self, path: str, output: Type[T]) -> Union[T, ErrorSchema]:
        return self.__call("GET", path, None, output)

    def post(self, path: str, payload: Optional[Schema], output: Type[T]) -> Union[T, ErrorSchema]:
        return self.__call("POST", path, payload, output)

    def put(self, path: str, payload: Optional[Schema], output: Type[T]) -> Union[T, ErrorSchema]:
        return self.__call("PUT", path, payload, output)

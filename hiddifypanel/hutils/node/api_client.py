from typing import Optional, Union, Type
from apiflask import Schema, fields
import traceback
import requests
from loguru import logger
from hiddifypanel.models import hconfig, ConfigEnum


class NodeApiErrorSchema(Schema):
    msg = fields.String(required=True)
    stacktrace = fields.String(required=True)
    code = fields.Integer(required=True)
    reason = fields.String(required=True)


class NodeApiClient():
    def __init__(self, base_url: str, apikey: Optional[str] = None, max_retry: int = 3):
        self.base_url = base_url if base_url.endswith('/') else base_url+'/'
        self.max_retry = max_retry
        self.headers = {'Hiddify-API-Key': apikey or hconfig(ConfigEnum.unique_id)}

    def __call(self, method: str, path: str, payload: Optional[Schema], output_schema: Type[Union[Schema, dict]]) -> Union[dict, NodeApiErrorSchema]:  # type: ignore
        retry_count = 1
        full_url = self.base_url + path.removeprefix('/')
        while 1:
            try:
                # TODO: implement it with aiohttp

                logger.trace(f"Attempting {method} request to node at {full_url}")

                # send request
                if payload:
                    response = requests.request(method, full_url, json=payload.dump(payload), headers=self.headers)
                else:
                    response = requests.request(method, full_url, headers=self.headers)

                # parse response
                response.raise_for_status()
                resp = response.json()
                if not resp:
                    err = NodeApiErrorSchema()
                    err.msg = 'Empty response'  # type: ignore
                    err.stacktrace = ''  # type: ignore
                    err.code = response.status_code  # type: ignore
                    err.reason = response.reason  # type: ignore
                    with logger.contextualize(payload=payload):
                        logger.warning(f"Received empty response from {full_url} with method {method}")
                    return err

                logger.trace(f"Successfully received response from {full_url}")
                return resp if isinstance(output_schema, type(dict)) else output_schema().load(resp)  # type: ignore

            except requests.HTTPError as e:
                if retry_count >= self.max_retry:
                    stack_trace = traceback.format_exc()
                    err = NodeApiErrorSchema()
                    err.msg = str(e)  # type: ignore
                    err.stacktrace = stack_trace  # type: ignore
                    err.code = response.status_code  # type: ignore
                    err.reason = response.reason  # type: ignore
                    with logger.contextualize(status_code=err.code, reason=err.reason, stack_trace=stack_trace, payload=payload):
                        logger.error(f"HTTP error after {self.max_retry} retries")
                        logger.exception(e)
                    return err

                logger.warning(f"Error occurred: {e} from {full_url} with method {method}, retrying... ({retry_count}/{self.max_retry})")
                retry_count += 1

    def get(self, path: str, output: Type[Union[Schema, dict]]) -> Union[dict, NodeApiErrorSchema]:
        return self.__call("GET", path, None, output)

    def post(self, path: str, payload: Optional[Schema], output: Type[Union[Schema, dict]]) -> Union[dict, NodeApiErrorSchema]:
        return self.__call("POST", path, payload, output)

    def put(self, path: str, payload: Optional[Schema], output: Type[Union[Schema, dict]]) -> Union[dict, NodeApiErrorSchema]:
        return self.__call("PUT", path, payload, output)

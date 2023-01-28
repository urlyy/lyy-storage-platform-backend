from fastapi import status
from fastapi.responses import JSONResponse, Response
from typing import Union
def success(*, message:str="SUCESS",data: Union[list, dict, str,None]=None) -> Response:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'code': 200,
            'message': message,
            'data': data,
        }
    )
def fail(*, message: str="BAD REQUEST", data: Union[list, dict, str,None]=None) -> Response:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'code': 500,
            'message': message,
            'data': data,
        }
    )


def warn(*, message: str = "BAD REQUEST", data: Union[list, dict, str, None] = None) -> Response:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'code': 400,
            'message': message,
            'data': data,
        }
    )

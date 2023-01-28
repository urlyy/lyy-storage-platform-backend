import time
import traceback
import uuid
from datetime import datetime

from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
import cv2
import numpy as np
from fastapi import FastAPI, Header, Body, Query, Form, applications, BackgroundTasks, UploadFile, HTTPException
import os
import uvicorn
import warnings

from requests import Request
from starlette.responses import StreamingResponse, FileResponse, Response

import search.img as img_search
import dao
from pojo.entity import User, Bucket, FileObject, BucketRule, ObjectRule
from pojo.response import success, fail, warn
from utils import _jwt, oss
from fastapi.middleware.cors import CORSMiddleware

from my_enum.my_enum import BucketACT, ObjectACT, BucketStatus, ObjectStatus

import logging

logger = logging.getLogger()

app = FastAPI(
    title="OSS-图像处理服务",
    version="1.0.0",
    description="全部接口",
    openapi_url="/api/api.json",
    docs_url="/docs"
)


def __img2cv2(img: UploadFile) -> np.ndarray:
    file_bytes: bytes = img.file.read()
    img_cv2 = cv2.imdecode(np.array(bytearray(file_bytes), dtype='uint8'), cv2.IMREAD_UNCHANGED)
    img.seek(0)
    return img_cv2


@app.get("/")
async def hello():
    return {"message": "Hello World", "swagger-url": "ip:port/docs"}


@app.post("/login", tags=["用户服务"], summary="登录")
async def login(account=Body(None), password=Body(None)):
    user = User(account, password)
    res = dao.login(user)
    if res:
        user.password = None
        token = _jwt.create_jwt(user.id)
        b = Bucket(user.id)
        dao.select_bucket_by_user_id(user, b)
        return success(
            message="登录成功",
            data={
                "id": user.id,
                "account": user.account,
                "token": token,
                "bucket_id": b.id,
                "bucket_name": b.name
            }
        )
    else:
        return warn(message="登录错误，请检查输入")


@app.post("/register", tags=["用户服务"], summary="注册")
async def register(account=Body(None), password=Body(None)):
    user = User(account, password)
    res = dao.register(user)
    if res is False:
        return warn(message="注册失败，用户名重复")
    bucket = Bucket(id=user.id, create_time=datetime.now())
    bucket.name = f"{uuid.uuid1()}-{user.id}"
    dao.insert_bucket(bucket, user)
    br = BucketRule(user.id, bucket.id, BucketACT.ADMIN.value)
    dao.insert_bucket_rule(br)
    return success(message="注册成功")


@app.get("/bucket", tags=["桶服务"], summary="获取桶信息")
async def get_bucket(bucket_id: int = Query(None), bucket_name: str = Query(None), token=Header(None)):
    user_id = _jwt.get_id(token)
    # 优先根据名称查
    if bucket_name is not None:
        b = Bucket(name=bucket_name)
        res = dao.select_bucket_by_name(b)
        if not res:
            return warn(message="bucket不存在或权限不足！")
        # 至少有这个桶
        else:
            # 查询是否开放
            if b.status == BucketStatus.PRIVATE.value:
                if user_id != b.user_id:
                    return warn(message="bucket不存在或权限不足！")
            else:
                # 查询权限
                br = BucketRule(user_id, b.id)
                res = dao.select_bucket_rule(br)
                if res:
                    return success(
                        data={"bucket_id": b.id, "bucket_name": b.name, "cur_size": b.size, "object_num": b.object_num,
                              "user_id": b.user_id,
                              "authority": br.act, "status": b.status, "create_time": b.create_time}
                    )
                else:
                    return warn(message="bucket不存在或权限不足！")
    else:
        # 我自己的
        b = Bucket(id=bucket_id)
        dao.select_bucket_by_id(b)
        if b.user_id != user_id:
            return fail(message="请不要使用桶id访问他人的桶")
        u = User(id=user_id)
        return success(
            data={"bucket_id": b.id, "bucket_name": b.name, "cur_size": b.size, "object_num": b.object_num,
                  "user_id": u.id,
                  "authority": BucketACT.ADMIN.value, "status": b.status, "create_time": b.create_time}
        )


@app.get("/{bucket_id}/objects", tags=["文件服务"], summary="获取文件列表")
async def get_objects(bucket_id: int, token: str = Header(None)):
    user_id = _jwt.get_id(token)
    u = User(id=user_id)
    b = Bucket(id=bucket_id)
    dao.select_bucket_by_id(b)
    objects = dao.select_objects(u, b)
    olist = []
    data = {}
    for o in objects:
        s = o.create_time
        o.create_time = s[0:s.rfind(".")]
        tmp = {"id": o.id, "name": o.name, "create_time": o.create_time, "bucket_id": o.bucket_id, "user_id": o.user_id,
               "type": o.type, "size": o.size, "content_type": o.content_type, "act": o.act, "status": o.status}
        olist.append(tmp)
    data["objects"] = olist
    return success(data=data)


@app.get("/img/search/{bucket_id}/txt", tags=["图像检索服务"], summary="文字搜图")
async def search_img_by_text(bucket_id=Query(None), text=Query(None), token=Header(None)):
    user_id = _jwt.get_id(token)
    b = Bucket(bucket_id)
    dao.select_bucket_by_id(b)
    k = dao.count_object_num(b)
    row_idxs = img_search.search_by_txt.search(b, text, k)
    o_list = []
    for row_idx in row_idxs:
        tmp_o = FileObject("image", row_idx, bucket_id=bucket_id)
        dao.select_object_by_id(tmp_o)
        if user_id != b.user_id and tmp_o.status == ObjectStatus.PRIVATE.value:
            continue
        if user_id == b.user_id:
            tmp_o.act = ObjectACT.ADMIN.value
        else:
            tmp_o.act = ObjectACT.ONLY_READ.value
        s = tmp_o.create_time
        tmp_o.create_time = s[0:s.rfind(".")]
        tmp = {"id": tmp_o.id, "name": tmp_o.name, "create_time": tmp_o.create_time, "bucket_id": tmp_o.bucket_id,
               "user_id": tmp_o.user_id,
               "type": tmp_o.type, "size": tmp_o.size, "content_type": tmp_o.content_type, "act": tmp_o.act,
               "status": tmp_o.status}
        o_list.append(tmp)
    return success(data={"objects": o_list})


@app.post("/img/search/{bucket_id}/img", tags=["图像检索服务"], summary="以图搜图")
async def search_img_by_img(bucket_id: int, file: UploadFile, token=Header(None)):
    user_id = _jwt.get_id(token)
    img_cv2 = __img2cv2(file)
    b = Bucket(bucket_id)
    k = dao.count_object_num(b)
    row_idxs = img_search.search_by_img.search(b, img_cv2, k)
    o_list = []
    for row_idx in row_idxs:
        tmp_o = FileObject("image", row_idx, bucket_id=bucket_id)
        dao.select_object_by_id(tmp_o)
        if user_id != b.user_id and tmp_o.status == ObjectStatus.PRIVATE.value:
            continue
        if user_id == b.user_id:
            tmp_o.act = ObjectACT.ADMIN.value
        else:
            tmp_o.act = ObjectACT.ONLY_READ.value
        s = tmp_o.create_time
        tmp_o.create_time = s[0:s.rfind(".")]
        tmp = {"id": tmp_o.id, "name": tmp_o.name, "create_time": tmp_o.create_time, "bucket_id": tmp_o.bucket_id,
               "user_id": tmp_o.user_id,
               "type": tmp_o.type, "size": tmp_o.size, "content_type": tmp_o.content_type, "act": tmp_o.act,
               "status": tmp_o.status}
        o_list.append(tmp)
    return success(data={"objects": o_list})


@app.post("/object", tags=["文件服务"], summary="上传文件")
async def add_object(file: UploadFile, bucket_id: int = Form(None), type=Form("file"), token=Header(None)):
    user_id = _jwt.get_id(token)
    u = User(id=user_id)
    b = Bucket(bucket_id)
    dao.select_bucket_by_id(b)
    o = FileObject(type, size=len(file.file.read()), name=f"{str(uuid.uuid1())}-{file.filename}",
                   content_type=file.content_type, create_time=datetime.now())
    if u.id == b.user_id:
        o.act = ObjectACT.ADMIN.value
        o.status = ObjectStatus.PRIVATE.value
    else:
        o.act = ObjectACT.ONLY_READ.value
        o.status = ObjectStatus.PUBLIC.value
    await file.seek(0)
    oss.upload(file.file.read(), b, o, content_type=file.content_type)
    res = dao.insert_object(u, b, o)
    tmp = {"id": o.id, "name": o.name, "create_time": str(o.create_time), "bucket_id": b.id,
           "user_id": o.user_id,
           "type": o.type, "size": o.size, "content_type": o.content_type, "act": o.act, "status": o.status}
    if type == "file":
        return success(message="上传普通文件成功", data={"object": tmp})
    else:
        await file.seek(0)
        img_cv2 = __img2cv2(file)
        await file.seek(0)
        img_search.search_by_img.add(b, o, img_cv2)
        img_search.search_by_txt.add(b, o, file.file.read())
        return success(message="上传图片成功", data={"object": tmp})


@app.get("/object/{bucket_id}/{object_id}", tags=["文件服务"], summary="下载文件")
async def download_object(bucket_id: int, object_id: int, preview: int = Query(0), token=Header(None)):
    # TODO 权限校验
    user_id = _jwt.get_id(token)
    u = User(id=user_id)
    b = Bucket(bucket_id)
    o = FileObject(id=object_id, type="")
    dao.select_bucket_by_id(b)
    dao.select_object_by_id(o)
    file_data = oss.download(b.name, o.name)
    if preview == 1:
        return Response(file_data)
    else:
        headers = {
            "Content-Disposition": 'attachment;filename=object'
        }
        return Response(file_data, headers=headers)


@app.get("/object/{bucket_id}/{object_id}/presigned-url", tags=["文件服务"], summary="产生文件临时访问链接")
async def get_object_presigned_url(bucket_id: int, object_id: int, token=Header(None), days: int = 0, hours: int = 0,
                                   minutes: int = 0):
    user_id = _jwt.get_id(token)
    u = User(id=user_id)
    # TODO 权限校验
    b = Bucket(bucket_id)
    o = FileObject(id=object_id, type="")
    dao.select_bucket_by_id(b)
    dao.select_object_by_id(o)
    url = oss.create_presigned_url(b, o, days, hours, minutes)
    return success(data={"url": url})


@app.delete("/object/{bucket_id}/{object_id}", tags=["文件服务"], summary="删除文件")
async def remove_object(bucket_id: int, object_id: int, token=Header(None)):
    # TODO 权限校验
    b = Bucket(id=bucket_id)
    o = FileObject(id=object_id, type="")
    dao.select_bucket_by_id(b)
    dao.select_object_by_id(o)
    oss.remove_object(b, o)
    dao.delete_object_by_id(b, o)
    return success()


@app.put("/bucket/{bucket_id}/status", tags=["桶服务"], summary="修改桶状态")
async def modify_bucket_status(bucket_id: int, bucket_status: int = Query(None)):
    b = Bucket(bucket_id, status=bucket_status)
    dao.update_bucket_status(b)
    return success()


@app.get("/bucket/{bucket_id}/rules", tags=["桶服务"], summary="获得桶的rules")
async def get_bucket_rule(bucket_id: int):
    bucket_rules = dao.select_bucket_rule_by_bucket_id(bucket_id)
    l = []
    for rule in bucket_rules:
        tmp = {
            "userId": rule.user_id,
            "act": rule.act
        }
        l.append(tmp)
    return success(data={"bucketRules": l})


@app.delete("/bucket/{bucket_id}/rule/{user_id}", tags=["桶服务"], summary="删除桶的rule")
async def remove_bucket_rule(bucket_id: int, user_id: int):
    br = BucketRule(user_id, bucket_id)
    dao.delete_bucket_rule(br)
    return success(message="删除成功")


@app.put("/bucket/{bucket_id}/rule/{user_id}", tags=["桶服务"], summary="修改rule的act")
async def modify_bucket_rule(bucket_id: int, user_id: int, act: str = Query(None)):
    br = BucketRule(user_id, bucket_id, act)
    dao.update_bucket_rule(br)
    return success(message="修改成功")


@app.post("/bucket/{bucket_id}/rule/{user_id}", tags=["桶服务"], summary="修改rule的act")
async def modify_bucket_rule(bucket_id: int, user_id: int, act: str = Query(None)):
    u = User(id=user_id)
    res = dao.select_user_by_id(u)
    if not res:
        return warn(message="用户不存在")
    else:
        br = BucketRule(user_id, bucket_id, act)
        dao.insert_bucket_rule(br)
        return success(message="新增成功")


@app.put("/object/{object_id}/status", tags=["桶服务"], summary="修改对象的状态")
async def modify_bucket_rule(object_id: int, status: int = Query(None)):
    o = FileObject("", id=object_id, status=status)
    dao.update_object_status(o)
    return success(message="修改对象状态成功")


def config_env():
    # 关掉一个警告
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    # 修改模型位置
    os.environ['TORCH_HOME'] = os.path.join("..", ".model")
    # 修改towhee文件位置
    os.environ['USERPROFILE'] = os.path.join("..")
    # 修改模型路径
    os.environ['TRANSFORMERS_CACHE'] = os.path.join('..', "huggingface", ".cache")
    # 关掉警告
    warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    # 解决无法访问Swagger的问题
    def swagger_monkey_patch(*args, **kwargs):
        return get_swagger_ui_html(
            *args, **kwargs,
            swagger_js_url='https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.10.3/swagger-ui-bundle.js',
            swagger_css_url='https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.10.3/swagger-ui.css'
        )

    applications.get_swagger_ui_html = swagger_monkey_patch

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return fail(message="输入异常或服务器出错")


@app.middleware("http")
async def logger_request(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 5))
    logger.info(f"访问记录:{request.method} url:{request.url}  耗时:{str(round(process_time, 5))}")
    return response


if __name__ == '__main__':
    config_env()
    uvicorn.run(app, port=9010)

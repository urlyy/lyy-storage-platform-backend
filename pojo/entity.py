import datetime


class User:
    id: int
    account: str
    password: str

    def __init__(self, account: str = "", password: str = "", id: int = 0):
        self.account = account
        self.password = password
        self.id = id


class Bucket:
    id: int
    name: str
    user_id:int
    size:int
    object_num:int
    status:int
    create_time:datetime

    def __init__(self, id: int = None, name: str = None,user_id:int=0,size:int=0,object_num:int=0,status:int="",create_time:datetime=None):
        self.id = id
        self.name = name
        self.user_id=user_id
        self.object_num = object_num
        self.size=size
        self.status=status
        self.create_time=create_time


class FileObject:
    id: int
    name: str
    bucket_id: int
    user_id: int
    size: int
    type: str
    create_time: datetime
    content_type:str
    act:str
    status:int

    def __init__(self, type: str, id: int = None, name: str = None, bucket_id: int = 0, user_id: int = 0,
                 size: int = 0,create_time:datetime=None,content_type="",act="",status:int=0):
        self.id = id
        self.name = name
        self.bucket_id = bucket_id
        self.user_id = user_id
        self.type = type
        self.size = size
        self.create_time = create_time
        self.content_type = content_type
        self.act =act
        self.status=status

    # def __str__(self):
    #     return "{\"id\": %d,\"name\": %s,\"bucket_id\": %d,\"user_id\": %d,\"size\": %d,\"type\": %s,\"createTime\": %s}"%(self.id,self.name,self.bucket_id,self.user_id,self.size,self.type,str(self.createTime))
class BucketRule:
    user_id:int
    bucket_id:int
    def __init__(self,user_id:int,bucket_id:int,act:str=None):
        self.user_id = user_id
        self.bucket_id = bucket_id
        self.act = act

class ObjectRule:
    user_id: int
    object_id: int
    def __init__(self,user_id:int,object_id:int,act:str=None):
        self.user_id = user_id
        self.object_id = object_id
        self.act = act
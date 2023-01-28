from enum import Enum
class BucketACT(Enum):
    ONLY_READ = "onlyRead"
    READ_WRITE = "readWrite"
    ADMIN = "admin"

# 桶主人有admin
# 其他能访问的人有只读
class ObjectACT(Enum):
    ONLY_READ = "onlyRead"
    ADMIN = "admin"

class BucketStatus(Enum):
    PUBLIC = 1
    PRIVATE = 0

class ObjectStatus(Enum):
    PUBLIC = 1
    PRIVATE = 0
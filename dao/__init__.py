# -*- coding: UTF-8 -*-
import json
import os
import sqlite3
from datetime import datetime

from pojo.entity import User, Bucket, FileObject, BucketRule, ObjectRule
from my_enum.my_enum import BucketACT, ObjectACT, BucketStatus, ObjectStatus


def con() -> sqlite3.Connection:
    return sqlite3.connect(os.path.join(os.getcwd(), "lyy-storage-platform.db"))


def login(u: User) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "select * from user where account=? AND password=?"
        c.execute(sql, (u.account, u.password))
        res = c.fetchone()
        if res is None:
            return False
        else:
            u.id = res[0]
            return True


def register(u: User) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "insert into user(account,password) values(?,?)"
        try:
            c.execute(sql, (u.account, u.password))
            conn.commit()
        except:
            return False
        sql2 = "select max(id) from user"
        c.execute(sql2)
        id = c.fetchone()[0]
        u.id = id
        return True


def insert_bucket(b: Bucket, u: User) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "insert into bucket(name,user_id,object_num,size,status,create_time) values(?,?,?,?,?,?)"
        c.execute(sql, (b.name, u.id,0,0,BucketStatus.PRIVATE.value,b.create_time))
        conn.commit()
        sql2 = "select max(id) from bucket"
        c.execute(sql2)
        id = c.fetchone()[0]
        b.id = id
        return True


def select_objects(u: User, b: Bucket) -> list:
    with con() as conn:
        c = conn.cursor()
        objects = []
        if u.id == b.user_id:
            sql = '''
                select *
                from file_object
                where user_id=? and bucket_id=?
                '''
            c.execute(sql, (u.id, b.id))
            rows = c.fetchall()
            for row in rows:
                o = FileObject(row[5], row[0], row[1], row[2], row[3], row[4], row[6], row[7], ObjectACT.ADMIN.value,row[8])
                objects.append(o)
        else:
            sql = '''
                    select *
                    from file_object as tmp
                    where tmp.bucket_id=? and tmp.status=?
                '''
            c.execute(sql, (b.id, ObjectStatus.PUBLIC.value))
            rows = c.fetchall()
            for row in rows:
                o = FileObject(row[5], row[0], row[1], row[2], row[3], row[4], row[6], row[7], ObjectACT.ONLY_READ.value,row[8])
                objects.append(o)
        return objects


def select_bucket_by_id(b: Bucket) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "select * from bucket where id=?"
        c.execute(sql, (b.id,))
        res = c.fetchone()
        b.name = res[1]
        b.user_id = res[2]
        b.object_num = res[3]
        b.size = res[4]
        b.status = res[5]
        b.create_time = res[6]
        return True

def count_object_num(b:Bucket)->int:
    with con() as conn:
        c = conn.cursor()
        sql = "select count(*) from file_object where bucket_id=?"
        c.execute(sql,(b.id,))
        res = c.fetchone()
        cnt = res[0]
        return cnt


def select_bucket_by_name(b: Bucket) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "select * from bucket where name=?"
        c.execute(sql, (b.name,))
        res = c.fetchone()
        if res == None:
            return False
        b.id = res[0]
        b.name = res[1]
        b.user_id = res[2]
        b.object_num = res[3]
        b.size = res[4]
        b.status = res[5]
        b.create_time = res[6]
        return True


def select_bucket_by_user_id(u: User, b: Bucket) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "select * from bucket where user_id=?"
        c.execute(sql, (u.id,))
        res = c.fetchone()
        b.id = res[0]
        b.name = res[1]
        b.user_id = res[2]
        b.object_num = res[3]
        b.size = res[4]
        b.status = res[5]
        b.create_time = res[6]
        return True


def insert_object(u: User, b: Bucket, o: FileObject) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql1 = "insert into file_object(name,bucket_id,user_id,size,type,create_time,content_type,status) values(?,?,?,?,?,?,?,?)"
        c.execute(sql1, (o.name, b.id, u.id, o.size, o.type, o.create_time, o.content_type,o.status))
        sql2 = "update bucket set size=size+?,object_num=object_num+1"
        c.execute(sql2, (o.size,))
        sql3 = "select max(id) from file_object"
        c.execute(sql3)
        conn.commit()
        id = c.fetchone()[0]
        o.id = id
        return True

def update_bucket_status(b: Bucket):
    with con() as conn:
        c = conn.cursor()
        sql = "update bucket set status=? where id=?"
        c.execute(sql, ( b.status, b.id))
        conn.commit()
        return True


def select_object_by_id(o: FileObject) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "select * from file_object where id=?"
        c.execute(sql, (o.id,))
        res = c.fetchone()
        o.name = res[1]
        o.type = res[5]
        o.content_type = res[7]
        o.size = res[4]
        o.create_time = res[6]
        o.status = res[8]
        return True


def update_object_status(b: FileObject):
    with con() as conn:
        c = conn.cursor()
        sql = "update file_object set status=? where id=?"
        c.execute(sql, ( b.status, b.id))
        conn.commit()
        return True

def delete_object_by_id(b: Bucket, o: FileObject) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "delete from file_object where id=?"
        c.execute(sql, (o.id,))
        sql = "update bucket set size=size-?,object_num=object_num-1 where id=?"
        c.execute(sql, (o.size, b.id))
        conn.commit()
        return True


def insert_bucket_rule(br:BucketRule):
    with con() as conn:
        c = conn.cursor()
        sql = "insert into bucket_rule(bucket_id, user_id, act) values (?,?,?)"
        c.execute(sql, (br.bucket_id,br.user_id,br.act))
        conn.commit()
        return True


def delete_bucket_rule(br:BucketRule):
    with con() as conn:
        c = conn.cursor()
        sql = "delete from bucket_rule where user_id=? and bucket_id=?"
        c.execute(sql, (br.user_id,br.bucket_id))
        conn.commit()
        return True


def update_bucket_rule(br:BucketRule):
    with con() as conn:
        c = conn.cursor()
        sql = "update bucket_rule set act=? where user_id=? and bucket_id=?"
        c.execute(sql, (br.act, br.user_id,br.bucket_id))
        conn.commit()
        return True


def select_bucket_rule(br: BucketRule) -> bool:
    with con() as conn:
        c = conn.cursor()
        sql = "select * from bucket_rule where user_id=? and bucket_id=? "
        c.execute(sql, (br.user_id, br.bucket_id))
        res = c.fetchone()
        if res is None:
            return False
        else:
            br.act = res[3]
        return True

def select_bucket_rule_by_bucket_id(bucket_id:int) -> list:
    l = []
    with con() as conn:
        c = conn.cursor()
        sql = "select * from bucket_rule where bucket_id=? "
        c.execute(sql, (bucket_id,))
        res = c.fetchall()
        for i in res:
            br = BucketRule(i[2],i[1],i[3])
            l.append(br)
        return l


def select_user_by_id(u:User)->bool:
    with con() as conn:
        c = conn.cursor()
        sql = "select * from user where id=?"
        res = c.execute(sql, (u.id,))
        res = res.fetchone()
        if res is None:
            return False
        return True
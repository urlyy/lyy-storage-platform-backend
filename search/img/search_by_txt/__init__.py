# encoding:utf-8
__all__ = ["add","search"]

import os

import cv2
import numpy as np
from towhee import dc
import horapy
from towhee.types import Image

from pojo.entity import Bucket,FileObject

index_dict = {}

dir_path = os.path.join(os.getcwd(), "index_data")
if os.path.exists(dir_path) is False:
    os.mkdir(dir_path)

class Index4TxtSearchImg:
    dimension=512
    def __init__(self,bucket_id:int):
        self.index_path = os.path.join(dir_path,f"img_search_by_txt-{bucket_id}.index")
        self.index = horapy.HNSWIndex(self.dimension, "usize")
        if os.path.exists(self.index_path):
            self.index.load(self.index_path)
    def add(self,e,idx):
        self.index.add(e,idx)
        self.index.build("euclidean")

    def search(self,e,k):
        return self.index.search(e,k)

    def __del__(self):
        self.index.dump(self.index_path)

def __set_dimension(x: np.ndarray) -> np.ndarray:
    x.shape = (x.shape[0], x.shape[1] if len(x.shape) > 1 else 1)
    x = x.reshape(1, x.shape[0])
    return x

def __extract_embeddings_txt(txt:str)->np.ndarray:
    embeddings = \
        dc['txt']([txt]) \
            .image_text_embedding.clip['txt', 'vec'](model_name='clip_vit_base_patch32', modality='text') \
            .tensor_normalize['vec', 'vec']() \
            .map(lambda x: __set_dimension(x.vec)) \
            .to_list()[0][0]
    # 只要一维
    return embeddings

def bytes2img(img_bytes:bytes):
    arr = np.asarray(bytearray(img_bytes), dtype=np.uint8)
    img =  cv2.imdecode(arr, -1)
    return Image(img, 'BGR')

def __extract_embeddings_img(img_bytes:bytes)->np.ndarray:

    embeddings = \
        dc['img']([img_bytes]) \
            .runas_op['img', 'img'](func=lambda b: bytes2img(b)) \
            .image_text_embedding.clip['img', 'vec'](model_name='clip_vit_base_patch32', modality='image') \
            .tensor_normalize['vec', 'vec']() \
            .map(lambda x: __set_dimension(x.vec)) \
            .to_list()[0][0]
    return embeddings



def search(bucket:Bucket,txt:str,k:int)->list:
    if index_dict.get(bucket.id) is None:
        index_dict[bucket.id]=Index4TxtSearchImg(bucket.id)
    e = __extract_embeddings_txt(txt)
    return index_dict.get(bucket.id).search(e,k)

def add(bucket:Bucket,object:FileObject,img:bytes):
    if index_dict.get(bucket.id) is None:
        index_dict[bucket.id]=Index4TxtSearchImg(bucket.id)
    e = __extract_embeddings_img(img)
    return index_dict.get(bucket.id).add(e, object.id)
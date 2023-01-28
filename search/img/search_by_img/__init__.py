# encoding:utf-8
__all__ = ["add","search"]

import os

import numpy as np
from towhee import dc
import horapy
from pojo.entity import Bucket,FileObject
from horapy import HNSWIndex

index_dict = {}

dir_path = os.path.join(os.getcwd(), "index_data")
if os.path.exists(dir_path) is False:
    os.mkdir(dir_path)

class Index4ImgSearchImg:
    dimension=2048
    def __init__(self,bucket_id:int):
        self.index = HNSWIndex(self.dimension, "usize")
        self.index_path = os.path.join(dir_path,f"img_search_by_img-{bucket_id}.index")
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

def __extract_embeddings(img:np.ndarray)->np.ndarray:
    embeddings = \
        dc['img']([img]) \
            .image_embedding.timm['img', 'vec'](model_name='resnet50')\
            .tensor_normalize['vec', 'vec']() \
            .map(lambda x: __set_dimension(x.vec)) \
            .to_list()[0][0]
    # 只要一维
    return embeddings

def search(bucket:Bucket,img:np.ndarray,k:int)->list:
    if index_dict.get(bucket.id) is None:
        index_dict[bucket.id]=Index4ImgSearchImg(bucket.id)
    e = __extract_embeddings(img)
    return index_dict.get(bucket.id).search(e,k)

def add(bucket:Bucket,object:FileObject,img:np.ndarray):
    if index_dict.get(bucket.id) is None:
        index_dict[bucket.id]=Index4ImgSearchImg(bucket.id)
    e = __extract_embeddings(img)
    index_dict.get(bucket.id).add(e, object.id)
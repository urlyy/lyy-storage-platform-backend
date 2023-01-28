__all__ = ["add_img","search_img_by_txt","search_img_by_img"]

import numpy as np
from towhee.types.image import Image
from search import img


def add_img(img_cv2: np.ndarray) -> dict:
    i = Image(img_cv2, mode="BGR")
    e4img_search_by_txt = img.search_by_txt.add(i)
    e4img_search_by_img = img.search_by_img.add(i)

    res = {
        "e4img_search_by_txt": e4img_search_by_txt,
        "e4img_search_by_img":e4img_search_by_img
    }
    return res


def search_img_by_txt(text: str) -> np.ndarray:
    e = img.search_by_txt.extract_embeddings_txt(text)
    return e

def search_img_by_img(img_cv2: np.ndarray) -> np.ndarray:
    e = img.search_by_img.extract_embeddings(img_cv2)
    return e


def e4img_detect_duplication():
    pass

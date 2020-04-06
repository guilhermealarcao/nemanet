# IMPORTS
import time
import numpy as np
import os
import cv2
import json
import copy
import tensorflow as tf
from libs.constants import *
from libs.ssim import SSIM
from object_detection.utils import label_map_util    ### CWH: Add object_detection path
from object_detection.utils import visualization_utils as vis_util
from object_detection.utils import helps
from skimage.measure import compare_ssim
import imutils
from PIL import Image
from matplotlib import pyplot as plt

# Helper code
def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)

# from object_detection.utils import visualization_utils as vis_util ### CWH: used for visualization


# import six.moves.urllib as urllib
# import tarfile
# # from PIL import Image




# Model Preparation

# What model to download.
# MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
# MODEL_FILE = MODEL_NAME + '.tar.gz'


# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = SETTINGS_DIR_MODEL+os.sep+SETTINGS_MODEL_NAME

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join(SETTINGS_DIR_MODEL+os.sep, SETTINGS_LABELMAP) ### CWH: Add object_detection path

# Download Model
# opener = urllib.request.URLopener()
# opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
# tar_file = tarfile.open(MODEL_FILE)
# for file in tar_file.getmembers():
#   file_name = os.path.basename(file.name)
#   if 'frozen_inference_graph.pb' in file_name:
#     tar_file.extract(file, os.getcwd())

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

# Load a (frozen) Tensorflow model into memory.
detection_graph = tf.compat.v1.Graph()
with detection_graph.as_default():
    od_graph_def = tf.compat.v1.GraphDef()
    with tf.compat.v1.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.compat.v1.import_graph_def(od_graph_def, name='')

    sess = tf.compat.v1.Session(graph=detection_graph)

image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
num_detections = detection_graph.get_tensor_by_name('num_detections:0')


class Object(object):

    def toJSON(self):
        return json.dumps(self.__dict__)


def comparar(before, after , boxes):
    _boxes = boxes[:]
    _centros = []
    vivos = 0;

    p1 = SSIM(before, after)
    cnts = p1.comparar()

    total = len(_boxes)
    # loop over the (unsorted) contours and draw them
    for (i, c) in enumerate(cnts):
        area = cv2.contourArea(c)
        if area > 45:
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            centro = {"x": cX, "y": cY }
            _centros.append(c)
            for box in _boxes:
                if dentro_do_quadrado(centro, box) == True:
                    _boxes.remove(box)
                    vivos = vivos+1
                    continue
            
    dados = {
        "vivo": vivos,
        "paralisado": (total - vivos),
        "total": total
    }
    return dados , _centros


def dentro_do_quadrado(centro, quadrado ):
    return ((  int(centro['x']) > int(quadrado['xmin']) and int(centro['x']) < int(quadrado['xmax'])) and  (int(centro['y']) > int(quadrado['ymin']) and int(centro['y']) < int(quadrado['ymax']) ))

def fazer_marcacao(before_image_path, threshold=0.50):
    before_image = cv2.imread(before_image_path)
    image_expanded = np.expand_dims(before_image, axis=0)

    (boxes, scores, classes, num) = sess.run(
    [detection_boxes, detection_scores, detection_classes, num_detections],
    feed_dict={image_tensor: image_expanded})
    
    total_box_achados=[]
    total_scores=[]
    
    classes = np.squeeze(classes).astype(np.int32)
    boxes = np.squeeze(boxes)
    scores = np.squeeze(scores)
    for i in range(boxes.shape[0]):
        if scores is None or scores[i] > threshold:
          box = tuple(boxes[i].tolist())
          total_box_achados.append(box)
          print(scores[i])
          total_scores.append(scores[i])

    item = Object()
    item.path = before_image_path
    item.achados = len(total_box_achados)
    item.score =  str(total_scores)
    item.position = helps.create_xml_annotatin(before_image, before_image_path , total_box_achados)
    return item.toJSON()


def get_objects(before_image_path, after_image_path, threshold=0.50):
    new_name = helps.nome_do_arquivo(before_image_path)
    before_image = cv2.imread(before_image_path)
    after_image = cv2.imread(after_image_path)
    image_expanded = np.expand_dims(before_image, axis=0)

    (boxes, scores, classes, num) = sess.run(
    [detection_boxes, detection_scores, detection_classes, num_detections],
    feed_dict={image_tensor: image_expanded})


    total_box_achados=[]
    classes = np.squeeze(classes).astype(np.int32)
    boxes = np.squeeze(boxes)
    scores = np.squeeze(scores)
    for i in range(boxes.shape[0]):
        if scores is None or scores[i] > threshold:
          box = tuple(boxes[i].tolist())
          total_box_achados.append(box)


    item = Object()
    total_box_convertidos = helps.convert_box_to_position(before_image , total_box_achados)
    # item.position = total_box_convertidos
    quantidade_dados , _centros = comparar(before_image, after_image , total_box_convertidos)
    
    # item.position = helps.create_xml_annotatin(image, before_image_path , total_box_achados)
    
    item.achados = int(len(total_box_achados))
    item.threshold = threshold
    item.path = before_image_path
    # item.centros = _centros
    item.gabarito = quantidade_dados
    return item.toJSON()

def get_teste(before_image_path, after_image_path, threshold=0.50):
    new_name = helps.nome_do_arquivo(before_image_path)
    before_image = cv2.imread(before_image_path)
    after_image = cv2.imread(after_image_path)
    image_expanded = np.expand_dims(before_image, axis=0)

    (boxes, scores, classes, num) = sess.run(
    [detection_boxes, detection_scores, detection_classes, num_detections],
    feed_dict={image_tensor: image_expanded})


    total_box_achados=[]
    classes = np.squeeze(classes).astype(np.int32)
    boxes = np.squeeze(boxes)
    scores = np.squeeze(scores)
    for i in range(boxes.shape[0]):
        if scores is None or scores[i] > threshold:
          box = tuple(boxes[i].tolist())
          total_box_achados.append(box)


    item = Object()
    total_box_convertidos = helps.convert_box_to_position(before_image , total_box_achados)
    # item.position = total_box_convertidos
    quantidade_dados , _centros = comparar(before_image, after_image , total_box_convertidos)
    
    # item.position = helps.create_xml_annotatin(image, before_image_path , total_box_achados)
    
    item.achados = int(len(total_box_achados))
    item.threshold = threshold
    item.path = before_image_path.split(os.sep)[-1]
    # item.centros = _centros
    item.gabarito = quantidade_dados
    print(item.toJSON())
    return item
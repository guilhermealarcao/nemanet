import object_detection_api
import os
import glob
import time
import json
import imutils
import cv2
from PIL import Image, ImageDraw
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree


url_list = sorted(glob.glob(os.path.join("/Users/guilhermealarcao/Dropbox/imgs_nematoide/Amostra03_77/", "*.jpg")))
for x in range(0,len(url_list) , 1):
	before = url_list[x]
	item = object_detection_api.fazer_marcacao(before , 0.99)
	print(item)



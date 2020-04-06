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



def gabarito(xml):
	shapes =[]
	parser = etree.XMLParser(encoding="utf-8")
	xmltree = ElementTree.parse(xml).getroot()
	gabarito = dict([('vivo', 0),('paralisado', 0),('total', 0)]);
	for object_iter in xmltree.findall('object'):
		bndbox = object_iter.find("bndbox")
		label = object_iter.find('name').text
		valor = gabarito.pop(label, 0)
		valor = valor + 1
		gabarito[label] = valor
		gabarito["total"] = gabarito.pop("total", 0) + 1
		xmin = int(float(bndbox.find('xmin').text))
		ymin = int(float(bndbox.find('ymin').text))
		xmax = int(float(bndbox.find('xmax').text))
		ymax = int(float(bndbox.find('ymax').text))
		points = {"xmin":xmin, "ymin":ymin, "xmax":xmax, "ymax":ymax}
		shapes.append(points)

	return gabarito , shapes


def get_name(nome):	
	return "/".join(nome.split(os.sep)[:-1]) , nome.split(os.sep)[-1].split(".")[0]

paralisados =0;
total = 0;
vivos = 0;
erro = 0;
certo = 0;
url_list = sorted(glob.glob(os.path.join("/Users/guilhermealarcao/Desktop/teste/121_80_3/", "*.jpg")))
for x in range(0,len(url_list) , 2):
	before = url_list[x]
	after = url_list[x+1]

	path,xml = get_name(before)
	texto_gabarito , shapes  = gabarito(path+"/"+xml+".xml")
	before_img = cv2.imread(before)
	path,xml = get_name(before)
	item = object_detection_api.get_objects(before , after , 0.99)


	vivos = vivos + item.gabarito['vivo']
	paralisados = paralisados + item.gabarito['paralisado']
	total = total + item.gabarito['total']
	
	if item.gabarito != texto_gabarito:
		erro = erro + 1
		print(before)
		print(after)
		print(item.gabarito)		
		print("=========acerto=============")
		print(texto_gabarito)
		print("======================")

		for i in range(0, len(item.position)):
			quadrado = item.position[i]
			cv2.rectangle(before_img, (quadrado['xmin'], quadrado['ymin']), (quadrado['xmax'], quadrado['ymax']), (36,255,12), 2)

		for i in range(0, len(shapes)):
			shape = shapes[i]
			cv2.rectangle(before_img, (shape['xmin'], shape['ymin']), (shape['xmax'], shape['ymax']), (255,255,255), 2)
			
		for i in range(0, len(item.centros)):
			M = cv2.moments(item.centros[i])
			cX = int(M["m10"] / M["m00"])
			cY = int(M["m01"] / M["m00"])
			ponto_movimento = {"x": cX, "y": cY }
			cv2.circle(before_img, (ponto_movimento['x'] , ponto_movimento['y']), 2, (0, 0, 255), 2)
			# cv2.drawContours(before_img, [item.centros[i]], -1, (0, 0, 255), 2)
			before_img = imutils.resize(before_img, width=1200)
			
		cv2.imshow('before', before_img)
		cv2.waitKey(3000)
	else:
		certo = certo + 1
	
	
# print(url_list)
print("erro:",erro)
print("certo:",certo)
print("paralisados:",paralisados)
print("vivos:",vivos)
print("total:",total)








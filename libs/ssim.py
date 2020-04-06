import imutils
from skimage.measure import compare_ssim
import numpy as np
import cv2


class SSIM:
	def __init__(self, before , after):
		#print("STEP 1: Load images")
		self.pontos_de_movimentacao =[]
		if type(before) == str:
			self.before = cv2.imread(before)
			self.after = cv2.imread(after)
		else:
			self.before = before
			self.after = after


	def marcarNaimg(self):
		cnts = self.comparar()
		for (i, c) in enumerate(cnts):
			area = cv2.contourArea(c)
			if area > 45:
				M = cv2.moments(c)
				cX = int(M["m10"] / M["m00"])
				cY = int(M["m01"] / M["m00"])
				center_coordinates = (cX, cY) 
				cv2.drawContours(self.before, [c], -1, (0, 255, 0), 2)
				cv2.circle(self.before, center_coordinates, 10, (0, 0, 255) , -1) 

	def viewImage(self):
		#print("STEP 7: Printing that difference")
		self.marcarNaimg()
		#print("STEP 8: View image")
		height, width = self.before.shape[:2]
		cv2.imshow('Display', imutils.resize(self.before, height = 900))
		cv2.waitKey(0)
		cv2.destroyAllWindows()

	def getPontosDeMovimentacao(self):
		return self.pontos_de_movimentacao
	
	def comparar(self):
		#print("STEP 2: Remove noises with blur")
		image = cv2.GaussianBlur(self.before, (21, 21), 0)
		image2 = cv2.GaussianBlur(self.after, (21, 21), 0)

		#print("STEP 3: Convert images to BGR")
		img1_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
		img2_bgr = cv2.cvtColor(image2, cv2.COLOR_RGB2BGR)

		#print("STEP 4: Compare two frame")
		teste1 = cv2.cvtColor(img1_bgr, cv2.COLOR_BGR2GRAY)
		teste2 = cv2.cvtColor(img2_bgr, cv2.COLOR_BGR2GRAY)
		(score, diff) = compare_ssim(teste1, teste2, full=True)

		#print("STEP 5: Calculation similarity:", score)
		diff = (diff * 255).astype("uint8")

		#print("STEP 6: Finding difference between frames")
		mask_bgr = cv2.threshold(diff, 200, 255, cv2.THRESH_BINARY_INV)[1]
		cnts = cv2.findContours(mask_bgr.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		return cnts
				


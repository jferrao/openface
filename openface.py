#!/usr/bin/env python
# -*- coding: UTF-8 -*-



# Import Python 3 default division operation behaviour
from __future__ import division

import os
import cStringIO
import mimetypes
from PIL import Image, ImageOps, ImageDraw
import cv



def index(req):
    image = myImage(req)
    req.content_type = image.mimetype
    
    return image.Render()



class myImage():
    
    request     = None
    args        = ()
    ifile       = None
    image       = None
    mimetype    = None
    faces       = None
    
    IMAGE_PATH              = os.path.dirname(os.path.abspath(__file__)) + "/images/"
    RESIZE_FACTOR           = 0.5
    
    source_orientation      = None
    destination_orientation = None
    
    
    
    def __init__(self, request):
        self.request = request
        self.__SetRequestParams(request.args)
        self.ifile = self.IMAGE_PATH + self.args['image'].replace('_', '/')
        self.mimetype = mimetypes.guess_type(self.ifile)[0]
    
        self.image = Image.open(self.ifile)
        self.__SetOrientation()

        method_name = 'Operation' + self.args['type'].lower().capitalize()
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            method = getattr(self, method_name)
            self.image = method(self.image, width=self.args['width'], height=self.args['height'])
    
    
    
    def Render(self):
        outputImage = cStringIO.StringIO()
        self.image.save(outputImage, "JPEG", quality=75)    
    
        outputImage.seek(0)
        return outputImage.read()



    def DetectFaces(self, image, resize_factor=1):
        if resize_factor < 1:
            # Trick: Reducing image to detect faces is faster then detection over the original one if this one is to big
            image = image.resize((int(image.size[0] * resize_factor), int(image.size[1] * resize_factor)), Image.ANTIALIAS)
        cvImage = cv.CreateImageHeader(image.size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(cvImage, image.tostring())
        cascade = cv.Load(os.path.dirname(__file__) + '/haarcascade_frontalface_alt.xml')
        return cv.HaarDetectObjects(cvImage, cascade, cv.CreateMemStorage(0), 1.1, 2, cv.CV_HAAR_DO_CANNY_PRUNING, (50,50))



    def GetTopmostFace(self, image, faces, resize_factor=1):
        topmost = image.size[1]
        for (x,y,w,h),n in faces:
            if topmost > y * int(1/resize_factor):
                topmost = y * int(1/resize_factor)

        return topmost
    
    
    
    def GetBottommostFace(self, image, faces, resize_factor=1):
        bottommost = 0
        for (x,y,w,h),n in faces:
            if bottommost < y * int(1/resize_factor):
                bottommost = y * int(1/resize_factor)

        return bottommost
    
    

    def GetBiggestFace(self, image, faces, resize_factor=1):
        hipo = 0
        for (x, y, w, h), n in faces:
            if hipo < (w * w) + (h * h):
                hipo = (w * w) + (h * h)
                center = y * int(1 / resize_factor)

        return center



    def OperationResize(self, image, **options):
        if options['width'] and not options['height']:
            options['height'] = (image.size[1] * options['width']) / image.size[0]
        elif options['height'] and not options['width']:
            options['width'] = (image.size[0] * options['height']) / image.size[1]
        #else:
        #    return image
    
        return image.resize((options['width'], options['height']), Image.ANTIALIAS)


    
    def OperationFit(self, image, centering=(0.5, 0.25), **options):
        if self.args['face'] and (self.source_orientation == 'v' and self.destination_orientation == 'h'):
            faces = self.DetectFaces(image, self.RESIZE_FACTOR)
            if faces:
                topmost = self.GetBiggestFace(image, faces, self.RESIZE_FACTOR)
                centering = (0.5, topmost / image.size[1])
    
        return ImageOps.fit(image, (options['width'], options['height']), Image.ANTIALIAS, 0, centering)



    def OperationOriginal(self, image, **options):
        if self.args['face']:
            faces = self.DetectFaces(image)
            draw = ImageDraw.Draw(image)
            for (x, y, w, h), n in faces:
                draw.rectangle([(x, y),(x + w, y + h)], outline = '#ff0000')
    
        return image



    def __SetRequestParams(self, args):
        args = args.split('&')
        data = {}
        for arg in args:
            temp = arg.split('=')
            data[temp[0]] =temp[1]
    
        if not 'width' in data:
            data['width'] = None
        else:
            data['width'] = int(data['width'])
        if not 'height' in data:
            data['height'] = None
        else:
            data['height'] = int(data['height'])
    
        if not 'face' in data:
            data['face'] = False
        else:
            if data['face'].lower() in ('true', '1'):
                data['face'] = True
            else:
                data['face'] = False
    
        if not 'type' in data: data['type'] = 'original'
    
        self.args = data



    def __SetOrientation(self):
        if self.image.size[0] / self.image.size[1] < 1:
            self.source_orientation = 'v'
        else:
            self.source_orientation = 'h'

        if self.args['width'] and self.args['height']:
            if self.args['width'] / self.args['height'] < 1:
                self.destination_orientation = 'v'
            else:
                self.destination_orientation = 'h'
    

    def GetImage(self):
        return self.image



#!/usr/bin/env python
from __future__ import print_function
import csv
import math
import os.path
import os

from PIL import Image, ImagePath
from PIL import TiffImagePlugin, TiffTags
from PIL import ImageDraw
# HACK
TiffTags.LIBTIFF_CORE.add(TiffImagePlugin.IMAGEDESCRIPTION)

import openslide
from ..models import LayerAndROIs

#import numpy
#from skimage.draw import polygon

# For running on HPC for large crop later
cropSizeLimit= 100000 * 10000000

def cropROI(slide, location, size, description, output_path, path):
    print('reading ROI...')
    image = slide.read_region(location, 0, size)
    print('writing...')

#    flat_path = path.tolist(True)
#    rr, cc = polygon(flat_path[1::2], flat_path[0::2])
#    mask = numpy.full((size[1], size[0]), 255, dtype=numpy.uint8)
#    mask[rr, cc] = 0
#    mask = Image.fromarray(mask, 'L')

    mask = Image.new('1', size, color=1)
    ImageDraw.Draw(mask).polygon(path, fill=0)

#    image.paste(Image.new('RGB', size), mask=mask)
# white background
    image.paste(Image.new('RGB', size, color=(255, 255, 255)), mask=mask)

    image.convert('RGB').save(output_path, compression='tiff_lzw',
                              description=description)


def process_single_image(in_file, prefix, postfix, output_folder, svs_path,
                         report_file, image_id, image_db, slurm_file):
    try:
        slide = openslide.OpenSlide(svs_path)
    except openslide.OpenSlideError:
        print('OpenSlide cannot open ' + svs_path);
        return

    description = slide.properties[openslide.PROPERTY_NAME_COMMENT]
    # print(slide.properties[openslide.PROPERTY_NAME_VENDOR])

    for roi in csv.reader(in_file):
        layer_name = roi[0]
        roi_index = int(roi[1])
        path = ImagePath.Path(list(zip(list(map(float, roi[2::2])),
                                       list(map(float, roi[3::2])))))

        bounding_box = path.getbbox()
        bounding_box = tuple(map(lambda n: int(math.floor(n)), bounding_box))
        size = (bounding_box[2] - bounding_box[0] + 1,
                bounding_box[3] - bounding_box[1] + 1)
        path.transform((1, 0, -bounding_box[0], 0, 1, -bounding_box[1]))

        print_args = (layer_name,) + size + bounding_box
        print('%s %dx%d (%d, %d) (%d, %d)' % print_args)

        roi_name =  '%s_%s_%s_%02d.tif' % (prefix, layer_name, postfix,
                                            roi_index) 
        report_file.write('%s,%s,%s\n' % (image_id, layer_name, roi_name))

        if size[0] * size[0] > cropSizeLimit:
            print_args = (image_id,) + size + bounding_box
            info = '{},{},{},{},{}\n'.format(prefix, postfix, svs_path, image_id,','.join(roi))
            slurm_file.write(info)
            report_file.write('Send image: %s size: %dx%d bbx: (%d, %d) (%d, %d) to HPC Slurm because of size is too large\n' % print_args)
        else:
            cropROI(slide, bounding_box[:2], size, description,
                    os.path.join(output_folder, roi_name), path)

        roiPath = os.path.join(output_folder, roi_name).replace('output', 'output_p').replace('.tif','.jpg')
        LayerAndROIs.objects.create(image=image_db, layer=layer_name, roi=roiPath)
    slide.close()

def startExtractSlurm(slurm_file, output_folder):
    # prefix, postfix, svs_path, image_id, layer_name, roi_index, vertices
    for roi in csv.reader(slurm_file):
        prefix = roi[0]
        postfix = roi[1]
        svs_path = roi[2]
        image_id = roi[3]
        layer_name = roi[4]
        roi_index = int(roi[5])
        try:
            slide = openslide.OpenSlide(svs_path)
        except openslide.OpenSlideError:
            print('OpenSlide cannot open ' + svs_path);
            return
        description = slide.properties[openslide.PROPERTY_NAME_COMMENT]
        path = ImagePath.Path(list(zip(list(map(float, roi[6::2])),
                                       list(map(float, roi[7::2])))))

        bounding_box = path.getbbox()
        bounding_box = tuple(map(lambda n: int(math.floor(n)), bounding_box))
        size = (bounding_box[2] - bounding_box[0] + 1,
                bounding_box[3] - bounding_box[1] + 1)
        path.transform((1, 0, -bounding_box[0], 0, 1, -bounding_box[1]))

        print_args = (layer_name,) + size + bounding_box
        print('%s %dx%d (%d, %d) (%d, %d)' % print_args)

        roi_name =  '%s_%s_%s_%02d.tif' % (prefix, layer_name, postfix,
                                            roi_index) 
        print('%s,%s,%s\n' % (image_id, layer_name, roi_name))

        cropROI(slide, bounding_box[:2], size, description,
                os.path.join(output_folder, roi_name), path)

        slide.close()

def startExtract(roiFile, prefix, postfix, outputFolder, SVSPath, reportFile, ImageID, imageDB, slurmFile):
    print()
    print("Local Processing " + roiFile)
    with open(roiFile) as roi_file, open(reportFile, 'a+') as report_file, open(slurmFile, 'a+') as slurm_file:
        process_single_image(roi_file, prefix, postfix,
                             outputFolder, SVSPath, report_file,
                             ImageID, imageDB, slurm_file)
    print("Local processing is done.")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--slurm', help='if it is a slurm job.', required=True)
    parser.add_argument('-sp', '--slurmfilepath', help='slurm cvs file path.', required=True)
    parser.add_argument('-d', '--directory', help='output directory.', required=True)
    args = parser.parse_args()

    if args.slurm:
        print()
        print("HPC Processing " + args.slurmfilepath)
        with open(args.slurmfilepath) as slurm_file:
            startExtractSlurm(slurm_file, args.directory)
        print("HPC processing is done.")            


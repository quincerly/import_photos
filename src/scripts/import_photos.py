#!/usr/bin/python3

import os
import sys
import fnmatch
import pyexiv2
import re
import shutil
import traceback
from optparse import OptionParser
import time
import subprocess
import json

from threading import Thread

from ImportPhotosGUI import SimpleGUI
from ImportPhotosGUI import ProgressBars

try:
    subprocess.check_output(['ffprobe', '--help'], stderr=subprocess.DEVNULL)
except:
    raise RuntimeError("Could not find ffprobe. Is ffmpeg installed?")

def GetMovieDate(filename):
    def tags_get_creation_time(json):
        fmts=[
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d %H:%M:%S',
        ] # Different time string formats I've found
        if 'tags' in json:
            tags=json['tags']
            if 'creation_time' in tags:
                for fmt in fmts:
                    try:
                        dt=time.strptime(tags['creation_time'], fmt)
                        return {"year":dt.tm_year,
                                "month":dt.tm_mon,
                                "day":dt.tm_mday}
                    except:
                        pass
        return None
    try:
        # Probe using FFMPEG and return result as JSON to parse
        probe=json.loads(subprocess.check_output(['ffprobe',
                                                  '-v', 'quiet',
                                                  filename,
                                                  '-print_format', 'json',
                                                  '-show_entries', 'stream=index,codec_type:stream_tags=creation_time:format_tags=creation_time']).decode())
    except:
        probe=None
    if probe is not None:
        # Return first creation_time found
        if 'format' in probe:
            dt=tags_get_creation_time(probe['format'])
            if dt is not None:
                return dt
        for stream in probe['streams']:
            dt=tags_get_creation_time(stream)
            if dt is not None:
                return dt
    return None

def GetImageDataAndCameraModel(filename):
    image = pyexiv2.Image(filename)
    md=image.read_exif()
    dt=time.strptime(md['Exif.Photo.DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
    #dt=md['Exif.Image.DateTime'].value
    date={"year":dt.tm_year,
          "month":dt.tm_mon,
          "day":dt.tm_mday}
    modelstr=""
    if "Exif.Image.Model" in md:
        modelstr=md["Exif.Image.Model"].strip().replace(" ","").replace("-","_")+"_"
    return date, modelstr

def GetThumbName(file_name):
    file_name, file_ext=os.path.splitext(file_name)

    thumb_file=file_name+'.thm'
    if os.path.exists(thumb_file):
        return thumb_file

    thumb_file=file_name+'.THM'
    if os.path.exists(thumb_file):
        return thumb_file

    return None

def ImportMedia(source_file, dest_root, overwrite):

    source_file=os.path.abspath(source_file)

    dir_name, file_name=os.path.split(source_file)
    file_name, file_ext=os.path.splitext(file_name)

    # For newer Canon EOS structure such as on R7
    eosnewmatch=re.match(r'.*/DCIM/(?P<dirnum>\d{3})EOS(?P<dirext>[\w\d]+)/(?P<camcode>[\w\d]{4})(?P<imnum>\d{4})', os.path.abspath(source_file))
    if eosnewmatch:
        canon_dir_num=eosnewmatch.group('dirnum')
        if file_ext.lower()==".mp4":
            date=GetMovieDate(source_file)
            modelstr={"R7": "CanonEOSR7_"}[eosnewmatch.group('dirext')]
        else:
            date, modelstr=GetImageDataAndCameraModel(source_file)
        dest_name="{}{}_{}{}".format(modelstr, canon_dir_num, file_name, file_ext.lower())
        mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
        return mess

    # For newer GoPro structure
    gopronewmatch=re.match(r'.*/DCIM/(?P<dirnum>\d+)GOPRO/(?P<camcode>\w+)(?P<imnum>\d+)', os.path.abspath(source_file))
    if gopronewmatch:
        gopro_dir_num=gopronewmatch.group('dirnum')
        if file_ext.lower()==".mp4":
            date=GetMovieDate(source_file)
            modelstr="GOPRO_"
        else:
            date, modelstr=GetImageDataAndCameraModel(source_file)
        dest_name="{}{}_{}{}".format(modelstr, gopro_dir_num, file_name, file_ext.lower())
        mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
        return mess

    # The number of the canon directory
    canon_dir_num=os.path.split(dir_name)[1].lower().replace('canon','')

    thumb_file=GetThumbName(source_file)

    #eosr7split=re.match(r'([\w\d]{4}(\d{4}))', file_name)
    canonsplit=re.match(r'(\w+)_(\d+)', file_name)
    sonysplit=re.match(r'(DSC)(\d+)', file_name)
    nikonsplit=re.match(r'(DSCN)(\d+)', file_name)
    goprosplitchap0=re.match(r'(GOPR)(\d+)', file_name)
    goprosplitchaps=re.match(r'(GP)(\d{2})(\d+)', file_name)
    olympussplit=re.match(r'(P\w?)(\d+)', file_name)

    if canonsplit:
        file_type=canonsplit.group(1).upper()
    elif sonysplit:
        file_type='DSC'
    elif nikonsplit:
        file_type='DSCN'
    elif goprosplitchap0:
        gpchap=0
        gpnum=int(goprosplitchap0.groups()[1])
        file_type='GOPROMVI'
    elif goprosplitchaps:
        gpchap=int(goprosplitchaps.groups()[1])
        gpnum=int(goprosplitchaps.groups()[2])
        file_type='GOPROMVI'
    elif olympussplit:
        file_type='Olympus'
    else:
        file_type='Unknown'

    if file_type=="GOPROMVI":
        date=GetMovieDate(source_file)
        dest_name="GoPro_{:04d}_{:02d}{:s}".format(gpnum, gpchap+1, file_ext.lower())
        mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
    elif file_type=='MVI':
        if thumb_file is not None:
            date, modelstr=GetImageDataAndCameraModel(thumb_file)
            dest_name=modelstr+canon_dir_num+'_'+file_name+file_ext.lower()
            mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
        else:
            date=GetMovieDate(source_file)
            if date is None:
                mess="ERROR FINDING DATE for '%s'" % source_file
            else:
                modelstr="CanonEOS70D_"
                dest_name=modelstr+canon_dir_num+'_'+file_name+file_ext.lower()
                mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
    elif file_type=='IMG':
        date, modelstr=GetImageDataAndCameraModel(source_file)
        #dest_name=modelstr+canon_dir_num+'_'+file_name+file_ext.lower()
        dest_name=modelstr+'_'+file_name+file_ext.lower()
        mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
    elif file_type[0:2]=='ST':
        date, modelstr=GetImageDataAndCameraModel(source_file)
        dest_name=modelstr+canon_dir_num+'_'+file_name+file_type[2]+file_ext.lower()
        mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
    elif file_type=='DSC':
        date, modelstr=GetImageDataAndCameraModel(source_file)
        dest_name=modelstr+file_name+file_ext.lower()
        mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
    elif file_type=='DSCN':
        date, modelstr=GetImageDataAndCameraModel(source_file)
        dest_name=modelstr+file_name+file_ext.lower()
        mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
    elif file_type=='Olympus':
        if file_ext.lower()==".mov":
            mess="Olympus MOV not handled %s" % source_file
            date=GetMovieDate(source_file)
            if date is None:
                mess="ERROR FINDING DATE for '%s'" % source_file
            else:
                modelstr="E_M10MarkIII_"
                dest_name=modelstr+file_name+file_ext.lower()
                mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
        else:
            date, modelstr=GetImageDataAndCameraModel(source_file)
            dest_name=modelstr+file_name+file_ext.lower()
            mess=ImportFile(source_file, dest_name, date, dest_root, overwrite)
    else:
        mess="Unknown file %s" % source_file
    #print(mess)

    return mess


def ImportFile(source_file, dest_name, date, dest_root, overwrite, test=False, move=False):

    if not dest_name:
        raise RuntimeError("Could not determine destination name for \"%s\"." % source_file)
    elif not date:
        raise RuntimeError("Could not determine date for \"%s\"." % source_file)

    dest_dir=os.path.join(dest_root,
                          "%04d" % date["year"],
                          "%02d" % date["month"],
                          "%04d_%02d_%02d" % (date["year"], date["month"], date["day"]))
    dest_file=os.path.join(dest_dir, dest_name)

    if os.path.exists(dest_file):
        if overwrite:
            if not test:
                copy_file_mkdir(source_file, dest_dir, dest_file)
            mess='Imported <b>overwriting</b> \"{}\"'.format(dest_file)
        else:
            mess='<b>Skipped existing</b> "{}"'.format(dest_file)
    else:
        if not test:
            copy_file_mkdir(source_file, dest_dir, dest_file, move=move)
        mess='Imported \"{}\"'.format(dest_file)

    return mess

def copy_file_mkdir(source_file, dest_dir, dest_file, move=False):

    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
        if not os.path.isdir(dest_dir):
            raise IOError("Could not create directory \"%s\"." % dest_dir)

    if move:
        shutil.move(source_file, dest_file)
    else:
        shutil.copyfile(source_file, dest_file)

def find_images(root_dirs):

    # Extensions to search for (case insensitive)
    exts=["mov", "jpg", "avi", "cr2", "cr3", "mp4", "orf"]
    #exts=["mov"]

    # Find all files with given extensions
    files=[]
    for root_dir in root_dirs:

        for roots, dirs, fils in os.walk(root_dir):
            for f in fils:
                for ext in exts:
                    if fnmatch.fnmatch(f.lower(), "*."+ext.lower()):
                        files.append(os.path.join(roots, f))

    return files

def main_cli():

    manual="""
    NAME
        import_photos

    SYNOPSIS
        import_photos directories

    DESCRIPTION
        Import photos and videos from specified location, e.g.

        import_photos /media/CANON_DC.

        Photos will be imported to /media/nas_dan/Photos in directories named according
        to date found in metadata.

    AUTHOR
        Dan Rolfe
    """

    # Process command line arguments and options
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-s", "--source", dest="source", default="/media/dan/EOS_DIGITAL",
                      help="Source root directory")
    parser.add_option("-d", "--dest", dest="dest", default="/media/nas_dan/Photos",
                      help="Destination root directory")
    parser.add_option("--no-gui", dest="gui", default=True, action="store_false",
                      help="Use graphical user interface")
    parser.add_option("--overwrite", dest="overwrite", default=False, action="store_true",
                      help="Overwrite existing files")
    (options, args) = parser.parse_args()

    if len(args) > 0:
        parser.error("Incorrect number of arguments")
        exit

    # Default source root directory
    default_root=options.source

    # Default destination directory root
    dest_root=options.dest

    if args:
        root_dirs=args
    else:
        if os.path.exists(default_root):
            root_dirs=[default_root]
        else:
            print(manual)
            sys.exit()

    # Find all the canon photo directories in the input directories
    images=sorted(find_images(root_dirs))

    # Import files
    if options.gui:
        bar=SimpleGUI.gui(title="Photo import")
    else:
        bar=ProgressBars.progress_bar(title="Photo import")

    bar.start()

    try:

        for i in range(len(images)):

            source_file=images[i]
            bar.set_text("Doing {:d} of {:d} ({:s}) ...".format(i+1, len(images), source_file))
            mess=ImportMedia(source_file, dest_root, options.overwrite)

            bar.set_frac((i+1.)/len(images))
            if options.gui: bar.new_message(mess)

        bar.set_text("Finished")


    except Exception as mess:

        if options.gui: bar.join()
        bar.close()
        traceback.print_exc()
        sys.exit(1)

    if options.gui:
        bar.enable_quit()
        bar.new_message("<b>Please close the window.....</b>")
        bar.join()
    else:
        bar.close()

"""timestamp accessing working"""

import os
import rawpy
import numpy as np
import exiftool
from datetime import datetime
from PIL import Image
from itertools import groupby
from operator import itemgetter
import cv2
import platform


def convert_to_rgba(input_path):
    """Convert an image file to RGBA format and save it."""

    # print("Input Path:",input_path)
    # print("Output Path:",output_path)
    try:
        # Check if the file is a CR3 RAW file
        if input_path.lower().endswith('.cr3'):
            # Open and process the CR3 file using rawpy
            with rawpy.imread(input_path) as raw:
                # Convert RAW to RGB
                rgb = raw.postprocess()

                # Convert numpy array to PIL Image
                pil_image = Image.fromarray(rgb)

                # Convert to RGBA
                rgba_image = pil_image.convert('RGBA')

                print("Image converted successfully.")
                return rgba_image
                # Save as PNG
                # rgba_image.save(output_path, 'PNG')
                # print(f"Successfully converted {input_path} to RGBA")
        else:
            # For other image formats, use PIL directly
            pil_image = Image.open(input_path).convert('RGBA')
            # pil_image.save(output_path, 'PNG')
            # print(f"Successfully converted {input_path} to RGBA")
            print("Other type of file image converted successfully.")
            return pil_image

    except Exception as e:
        print(f"Error converting image: {e} of image: {input_path}")


def extract_time_from_image(file_path):

    """Extract the timestamp from an image file using exiftool."""
    try:
        if platform.system() == "Windows":
            exiftool_path = "exiftool.exe"
        else:
            exiftool_path = "exiftool"
        with exiftool.ExifToolHelper(executable=exiftool_path) as et:
            metadata = et.get_metadata(file_path)
            timestamp = metadata[0].get('EXIF:DateTimeOriginal')
            if timestamp:
                date_time = datetime.strptime(timestamp, '%Y:%m:%d %H:%M:%S')
                return date_time
            else:
                print(f"Timestamp not found in {file_path}.")
                return None
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {e}")
        return None


def blend_images(image_paths, output_path):
    """Blend a list of images using PIL."""
    # Open all images and convert to RGBA
    print("Image Paths: ",image_paths)
    images = [convert_to_rgba(path) for path in image_paths]
    print("One batch of file converted to rgba.")
    if not images:
        print("No valid images to blend.")
        return

    # Resize all images to the same size (if needed)
    # width, height = images[0].size
    # for i in range(1, len(images)):
    #     images[i] = images[i].resize((width, height))

    # Blend the images with equal weights
    blended_image = images[0]
    for i in range(1, len(images)):
        alpha = 1.0 / (i + 1)  # Equal weight blending
        blended_image = Image.blend(blended_image, images[i], alpha)

    # Save the blended image as PNG
    blended_image.save(output_path)


def blend_raw_images(image_paths, output_path):
    """
    Blends multiple RAW images into one and saves the resulting image.

    Parameters:
        image_paths (list of str): List of file paths to the RAW images to be blended.
        output_path (str): File path to save the blended image.

    Returns:
        None
    """

    processed_images = []

    # Read and process each RAW image
    for image_path in image_paths:
        #last tested code on 4/1/25
        # with rawpy.imread(image_path) as raw:
        #     image = raw.postprocess()
        #test code of 4/1/25
        try:
            with rawpy.imread(image_path) as raw:
                image = raw.postprocess()
        except rawpy.LibRawDataError as e:
            print(f"Error processing {image_path}: {e}")
            continue

            # Convert from RGB to BGR for OpenCV compatibilit
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        processed_images.append(image.astype(np.float32))

    # Resize images to match the first image's dimensions
    height, width, _ = processed_images[0].shape
    processed_images = [cv2.resize(image, (width, height)) for image in processed_images]

    # Blend images
    blended = np.mean(processed_images, axis=0)
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    # Save the blended image
    cv2.imwrite(output_path, blended)


def process_folder(input_folder, output_folder):
    count = 0
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get all image files in the input folder
    image_files = []
    for root, _, files in os.walk(input_folder):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.cr2', '.cr3', '.nef', '.dng')):
                image_files.append(os.path.join(root, f))

    print("Total Image files in folders:",len(image_files))
    # Extract timestamps and pair them with file paths
    image_files_with_time = [(f, extract_time_from_image(f)) for f in image_files]
    image_files_with_time = [item for item in image_files_with_time if item[1] is not None]  # Filter out files without timestamps
    print(f"Timestamp of {len(image_files_with_time)} files has been captured.")
    image_files_with_time.sort(key=itemgetter(1))
    print("Timestamp of all files has been captured.")

# ---------------->>>>   Check this code there is some problem down
    # Group images by timestamp
    for _, group in groupby(image_files_with_time, key=itemgetter(1)):
        group_list = list(group)
        if len(group_list) > 1:
            times = [item[1] for item in group_list]
            if (times[-1] - times[0]).total_seconds() <= 5:  # Group images taken within 5 seconds
                image_paths = [item[0] for item in group_list]
                output_path = os.path.join(output_folder, f"blended_{group_list[0][1].strftime('%Y%m%d_%H%M%S')}.png")
                blend_raw_images(image_paths, output_path)
                count += 1
                print(f"Group {count} of {image_paths} images has been blended.")
    
    return 1

def process_folderY(input_folder, output_folder):
    count = 0
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get all image files in the input folder
    image_files = []
    for root, _, files in os.walk(input_folder):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.cr2', '.cr3', '.nef', '.dng')):
                image_files.append(os.path.join(root, f))

    yield f"Total Image files in folders: {len(image_files)}"
    # Extract timestamps and pair them with file paths
    image_files_with_time = [(f, extract_time_from_image(f)) for f in image_files]
    image_files_with_time = [item for item in image_files_with_time if item[1] is not None]  # Filter out files without timestamps
    yield f"Timestamp of {len(image_files_with_time)} files has been captured."
    image_files_with_time.sort(key=itemgetter(1))
    yield "Timestamp of all files has been captured."

    # Group images by timestamp
    for _, group in groupby(image_files_with_time, key=itemgetter(1)):
        group_list = list(group)
        if len(group_list) > 1:
            times = [item[1] for item in group_list]
            if (times[-1] - times[0]).total_seconds() <= 5:  # Group images taken within 5 seconds
                image_paths = [item[0] for item in group_list]
                output_path = os.path.join(output_folder, f"blended_{group_list[0][1].strftime('%Y%m%d_%H%M%S')}.png")
                blend_raw_images(image_paths, output_path)
                count += 1
                yield f"Group {count} of {image_paths} images has been blended."

    yield "Processing complete."
    


if __name__ == "__main__":
    # input_folder = r"C:\Users\risha\Documents\app\auto_image_filter\exp_data_folder\images3"
    # output_folder = r"C:\Users\risha\Documents\app\auto_image_filter\exp_data_folder\output_data"
    input_folder = input("Enter the input folder path: ")
    output_folder = input("Enter the output folder path: ")
    # process_folder(input_folder, output_folder)
    for status in process_folderY(input_folder, output_folder):
        print(status)

""" Check Point: cr2 and cr3 successfully converted to enfused images but other DNG and NEF not even recognised.
    
    Recheck result:
        No problem in conversion of DNG or NEF to RGBA problem found.
        
    Correction: there was problem of misssing extension on endswith code.
    
    Resolved successfull and running on all types of files to enfuse stage
    
    Problem check point 2: for DNG and NEF image files it decrease size too much.

    Date: 12/8
    test Update 1: blended_image.save(output_path, 'PNG', compress_level=0) updated for explicitly turn off the compression
    Result: it doesn't work

    Date:12/8
    Test Update 2: updated 24 line to be more specific rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=16)
    Result: Didn't worked
    
    Date:12/8
    Test: Run blend code independently on dng files , it seems blend function is responsible for compression 
    
    Date"3/1/25
    Test 1: Run code after updating blend . main update is converting image rgb to bgr so it could be compatible with cv2
    Test 2: on raw2000 data there is error come when we try to process image _MG_4744, _MG_4745, _MG_4746
    Action 2_1: Trying to subdivide data and work on individual as there is error of corrupted data.
    Action 2_2: Deleting this file to check if these only come on these files or other as well.
    Result: Still not working .It seems there problem with computer's delete software. As last time when i delete something it still not visible on interface.
    
    Date: 4/1/25
    Test 1: I put the exceptionn handling for image = raw.postprocess() line code .
    Result: It gives detail of which image is exactly corrupted.
            Image is really corrupted when I open that exact file.
            
    Date: 16/1/25
    Test 1: I run this code again on raw2000 folder test no.3 . 
    Result: 
             - Same as before. Few corrupted files. 
             - And it stopped at group no 317. 
             - Last image file processed was DSC_8880.NEF
    Action: I deleted all corrupted image files from folder.
    Next Expected Action: To re run the code again.
    
    Date: 18/1-25
    
        Test 1: Rerun the code after removing corrupted files
        Result:
             - Processing stopped at group 315.
             - Last image file processed was DSC_8880.NEF
        Action: I created a seprate folder filled with those undetected images.
        
        Test 2: Re-run the code on undetected images of raw2000.
        Result: 
                - Processed all images.
                

        
    
"""
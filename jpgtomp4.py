import cv2
import os
import re

def extract_number(filename):
    return int(re.search(r'\d+', filename).group())

# Specify the directory containing the JPEG images
image_folder = 'videos/images'
video_name = 'videos/output.mp4'

# Retrieve the image files from the folder
images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
# Sort the images by their name to ensure they are in the correct order
#images.sort()
images = sorted(images, key=extract_number)

# Read the first image to get its dimensions
sample_image = cv2.imread(os.path.join(image_folder, images[0]))
height, width, layers = sample_image.shape

# Define the codec and create the VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video = cv2.VideoWriter(video_name, fourcc, 30, (width, height))

# Loop through the images and add them to the video
for image in images:
    img_path = os.path.join(image_folder, image)
    frame = cv2.imread(img_path)
    video.write(frame)

# Release the VideoWriter object
video.release()

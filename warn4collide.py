import numpy as np
import os
import sys
import tensorflow as tf
import cv2
import imutils
import time
from sklearn.metrics import pairwise
from imutils.video import FPS
import pdb
import re
import time


# sys.path.append('../../research')

from utils import ops as utils_ops
from utils import label_map_util
from utils import visualization_utils as vis_util

font = cv2.FONT_HERSHEY_SIMPLEX


utils_ops.tf = tf.compat.v1
tf.gfile = tf.io.gfile
PATH_TO_LABELS = 'C:/Users/holli/Desktop/Vehicle-Warning-Indicator-System/my_model/labels.pbtxt'
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)

#model_name = 'centernet_mobilenetv2_fpn_od'  DOESN'T RUN, wrong model output format
#model_name = 'centernet_mobilenetv2_fpn_od'  DOESN'T RUN, 
#model_name = 'ssd_mobilenet_v3_large_coco_2020_01_14' DOESN'T RUN


#model_name = 'ssd_mobilenet_v1_0.75_depth_300x300_coco14_sync_2018_07_03'
#model_name = 'centernet_hg104_512x512_coco17_tpu-8'
model_name = 'ssdlite_mobilenet_v2_coco_2018_05_09'
#model_name = 'ssd_mobilenet_v2_coco_2018_03_29'
model_dir =  "my_model/" + model_name + "/saved_model"
detection_model = tf.saved_model.load(str(model_dir))
detection_model = detection_model.signatures['serving_default']



print(detection_model.inputs)
print(detection_model.output_dtypes)
print(detection_model.output_shapes)

crash_count_frames = 0
# max_collide_area = 0
def estimate_collide(output_dict,height,width,image_np):
  global crash_count_frames
  vehicle_crash = 0
  max_curr_obj_area = 0
  centerX = centerY = 0
  details = [0 , 0 , 0 , 0]
  for ind,scr in enumerate(output_dict['detection_classes']):
    if scr==2 or scr==3 or scr==4 or scr==6 or scr==8:
      ymin, xmin, ymax, xmax = output_dict['detection_boxes'][ind]
      score = output_dict['detection_scores'][ind]
      if score>0.5:
        obj_area = int((xmax - xmin)*width * (ymax - ymin)*height)
        if obj_area > max_curr_obj_area:
          max_curr_obj_area = obj_area
          details = [ymin, xmin, ymax, xmax]

  #print(max_curr_obj_area)
  centerX , centerY = (details[1] + details[3])/2 , (details[0] + details[2])/2
  if max_curr_obj_area>70000:
    if (centerX < 0.2 and details[2] > 0.9) or (0.2 <= centerX <= 0.8) or (centerX > 0.8 and details[2] > 0.9):
      vehicle_crash = 1
      crash_count_frames = 15

  if vehicle_crash == 0:
    crash_count_frames = crash_count_frames - 1
    
  # cv2.putText(image_np, "{}  {}  {}  ".format(str(centerX)[:6],str(details[2])[:6],max_curr_obj_area) ,(50,100), font, 1.2,(255,255,0),2,cv2.LINE_AA)
  #print('1')
  if crash_count_frames > 0:
    if max_curr_obj_area <= 10000:
      print("YOU ARE GETTING CLOSER")
      cv2.putText(image_np,"YOU ARE GETTING CLOSER" ,(50,50), font, 1.2,(0,165,255),2,cv2.LINE_AA)
    elif max_curr_obj_area > 10000:
    #FOR CROPPED IMAGES #elif max_curr_obj_area > 300000 
      print("BRAKE BRAKE BRAKE!!")
      cv2.putText(image_np,"BRAKE BRAKE BRAKE!!" ,     (50,50), font, 1.2,(0,25,255),2,cv2.LINE_AA)







def run_inference_for_single_image(model, image):
  image = np.asarray(image)
  input_tensor = tf.convert_to_tensor(image)
  input_tensor = input_tensor[tf.newaxis,...]


  # output_dict is a dict  with keys detection_classes , num_detections , detection_boxes(4 coordinates of each box) , detection_scores for 100 boxes
  output_dict = model(input_tensor)

  # num_detections gives number of objects in current frame
  num_detections = int(output_dict.pop('num_detections'))


  # output_dict is a dict  with keys detection_classes , detection_boxes(4 coordinates of each box) , detection_scores for num_detections boxes
  output_dict = {key:value[0, :num_detections].numpy() 
                 for key,value in output_dict.items()}
  # adding num_detections that was earlier popped out
  output_dict['num_detections'] = num_detections
  # converting all values in detection_classes as ints.
  output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)
  # print(6,output_dict)

  return output_dict





def show_inference(model, image_path):
  # the array based representation of the image will be used later in order to prepare the
  # result image with boxes and labels on it.
  # image_np = np.array(Image.open(image_path))
  image_np = np.array(image_path)
  height,width,channel = image_np.shape

  # Actual detection.
  output_dict = run_inference_for_single_image(model, image_np)
  estimate_collide(output_dict,height,width,image_np)

  vis_util.visualize_boxes_and_labels_on_image_array(
      image_np,
      output_dict['detection_boxes'],
      output_dict['detection_classes'],
      output_dict['detection_scores'],
      category_index,
      instance_masks=output_dict.get('detection_masks_reframed', None),
      use_normalized_coordinates=True,
      line_thickness=8)

  return image_np



def extract_number(filename):
    return int(re.search(r'\d+', filename).group())


def jpgtomp4():
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






#pdb.set_trace()
cap=cv2.VideoCapture('C:/Users/holli/Desktop/Vehicle-Warning-Indicator-System/videos/footage.mp4')
time.sleep(2.0)


#cap.set(1,379*30)

#fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#out1 = cv2.VideoWriter('output.mp4', fourcc, 3.0, (int(cap.get(3)),int(cap.get(4))))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out1 = cv2.VideoWriter('videos/output.mp4', fourcc, 30, (int(cap.get(3)), int(cap.get(4))))

fps = FPS().start()

inference_times = []


ctt = 0
while True:
    (grabbed, frame) = cap.read()
    #print('frame',frame.shape)
    frame = frame[ :-150, : , :]
    #print(frame.shape)
    #print(ctt)
    ctt = ctt + 1
    if ctt==350:
      break

    start_time = time.time()

    frame=show_inference(detection_model, frame)
    end_time = time.time()
    inference_times += [end_time - start_time]
    
    

    
    cv2.imwrite('videos/images/' + str(ctt) + '.jpg', frame)
    #cv2.imshow("version", frame)
    out1.write(frame)
    fps.update()
    #key=cv2.waitKey(1)
    #if key & 0xFF == ord("q"):
    #  break
        
# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
print('avg inference time:', np.mean(inference_times))
cap.release()
out1.release()
cv2.destroyAllWindows() 


jpgtomp4()





# a.mp4(25)   56    74  110
# b.mp4(24)  4  270   292  368
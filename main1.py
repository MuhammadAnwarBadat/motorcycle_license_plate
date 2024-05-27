import os
import cv2
import pytesseract
from my_functions import *

# Create directories if they don't exist
if not os.path.exists('Number Plates'):
    os.makedirs('Number Plates')
if not os.path.exists('Preprocessed Plates'):
    os.makedirs('Preprocessed Plates')

source = 'test_video_6.mp4'

save_video = True  # want to save video? (when video as source)
show_video = True  # set true when using video file
save_img = False  # set true when using only image file to save the image
# when using image as input, lower the threshold value of image classification

# Saving video as output
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output.mp4', fourcc, 20.0, frame_size)

rider_detected = False
helmet_detected = False
plate_detected = False
plate_images = []

cap = cv2.VideoCapture(source)
while(cap.isOpened()):
    ret, frame = cap.read()
    if ret == True:
        frame = cv2.resize(frame, frame_size)  # resizing image
        orifinal_frame = frame.copy()
        frame, results = object_detection(frame) 

        rider_list = []
        head_list = []
        number_list = []

        for result in results:
            x1, y1, x2, y2, cnf, clas = result
            if clas == 0:
                rider_list.append(result)
                rider_detected = True
            elif clas == 1:
                head_list.append(result)
            elif clas == 2:
                number_list.append(result)

        for rdr in rider_list:
            time_stamp = str(time.time())
            x1r, y1r, x2r, y2r, cnfr, clasr = rdr
            for hd in head_list:
                x1h, y1h, x2h, y2h, cnfh, clash = hd
                if inside_box([x1r, y1r, x2r, y2r], [x1h, y1h, x2h, y2h]):  # if this head inside this rider bbox
                    try:
                        head_img = orifinal_frame[y1h:y2h, x1h:x2h]
                        helmet_present = img_classify(head_img)
                    except:
                        helmet_present = [None, 0]

                    if helmet_present[0] == True:  # if helmet present
                        helmet_detected = True
                        frame = cv2.rectangle(frame, (x1h, y1h), (x2h, y2h), (0, 255, 0), 1)
                        frame = cv2.putText(frame, f'Helmet: Yes ({round(helmet_present[1], 1)})', (x1h, y1h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    elif helmet_present[0] == None:  # Poor prediction
                        frame = cv2.rectangle(frame, (x1h, y1h), (x2h, y2h), (0, 255, 255), 1)
                        frame = cv2.putText(frame, f'Helmet: Uncertain ({round(helmet_present[1], 1)})', (x1h, y1h), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    elif helmet_present[0] == False:  # if helmet absent 
                        helmet_detected = False
                        frame = cv2.rectangle(frame, (x1h, y1h), (x2h, y2h), (0, 0, 255), 1)
                        frame = cv2.putText(frame, f'Helmet: No ({round(helmet_present[1], 1)})', (x1h, y1h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                        
                        # Print detection summary and terminate
                        print("Rider: Detected")
                        print("Helmet: Not Detected")
                        cap.release()
                        cv2.destroyAllWindows()
                        print('Video processing terminated')
                        exit(0)

            for num in number_list:
                x1_num, y1_num, x2_num, y2_num, conf_num, clas_num = num
                if inside_box([x1r, y1r, x2r, y2r], [x1_num, y1_num, x2_num, y2_num]):
                    try:
                        num_img = orifinal_frame[y1_num:y2_num, x1_num:x2_num]
                        cv2.imwrite(f'Number Plates/{time_stamp}_{conf_num}.jpg', num_img)
                        plate_detected = True
                        plate_images.append(f'Number Plates/{time_stamp}_{conf_num}.jpg')
                        frame = cv2.putText(frame, f'Plate: Detected', (x1_num, y1_num - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                    except:
                        print('could not save number plate')

        if save_video:  # save video
            out.write(frame)
        if save_img:  # save img
            cv2.imwrite('saved_frame.jpg', frame)
        if show_video:  # show video
            frame = cv2.resize(frame, (900, 450))  # resizing to fit in screen
            cv2.imshow('Frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
    else:
        break

cap.release()
cv2.destroyAllWindows()
print('Video processing completed')

# Function to preprocess and extract text from number plate images
def extract_text_from_images(image_paths):
    plate_texts = []
    for image_path in image_paths:
        img = cv2.imread(image_path)
        # Preprocess the image for better OCR accuracy
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        enhanced_img = cv2.convertScaleAbs(gray, alpha=2, beta=0)
        blurred = cv2.GaussianBlur(enhanced_img, (5, 5), 0)
        _, binary_img = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Save the preprocessed image
        preprocessed_image_path = image_path.replace('Number Plates', 'Preprocessed Plates')
        cv2.imwrite(preprocessed_image_path, binary_img)
        
        text = pytesseract.image_to_string(binary_img, config='--psm 8')
        plate_texts.append(text.strip())
    return plate_texts

# Extract text from captured number plate images
plate_texts = extract_text_from_images(plate_images)

# Print detection summary
if rider_detected:
    print("Rider: Detected")
else:
    print("Rider: Not Detected")

if helmet_detected:
    print("Helmet: Detected")
else:
    print("Helmet: Not Detected")

if plate_detected:
    print("Plate: Detected")
    for text in plate_texts:
        print(f'Plate Text: {text}')
else:
    print("Plate: Not Detected")


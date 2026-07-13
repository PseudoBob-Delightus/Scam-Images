from io import BytesIO

import cv2
import numpy as np

def is_much_wider_than_tall(img: np.ndarray) -> bool:
    height, width, _ = img.shape
    return True if (width > (height * 1.4) ) else False

def split_two_images(image: BytesIO) -> list[BytesIO]:
    output: list[BytesIO] = [image]
    try:
        img = cv2.imdecode(np.frombuffer(image.read(), np.uint8), 1)
        if not is_much_wider_than_tall(img):
            return output
        height, width, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        start_col = int(width * 0.20)
        end_col = int(width * 0.80)
        smoothed_gray = cv2.GaussianBlur(gray, (15, 1), 0)
        column_brightness = np.mean(smoothed_gray[:, start_col:end_col], axis=0)
        brightness_gradients = np.abs(np.diff(column_brightness))
        best_relative_cut = np.argmax(brightness_gradients)
        cut_x = start_col + best_relative_cut
        crops = [img[0:height, 0:cut_x], img[0:height, cut_x:width]]
        for crop in crops:
            out_image = cv2.imencode(".png", crop)[1].tobytes()
            output.append(BytesIO(out_image))
        return output
    except Exception:
        return output

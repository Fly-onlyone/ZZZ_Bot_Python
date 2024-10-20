import cv2
import numpy as np
import os
from playwright.sync_api import Locator


class ImageProcessor:
    def __init__(self, button, path):
        self.button = button
        self.path = path
        self.capture_button_screenshot(button, path)

    @staticmethod
    def compare_images(image1_path, image2_path):
        # Read the images
        img1 = cv2.imread(image1_path)
        img2 = cv2.imread(image2_path)

        # Resize images to the same size for comparison (optional if sizes differ)
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # Compute the difference between the images
        difference = cv2.absdiff(img1, img2)

        # Convert the difference image to grayscale
        gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

        # Apply a binary threshold to the grayscale difference image
        _, threshold_diff = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

        # Calculate the percentage of different pixels
        non_zero_count = np.count_nonzero(threshold_diff)
        total_pixels = threshold_diff.size
        difference_percentage = (non_zero_count / total_pixels) * 100

        return difference_percentage

    def detect_button_state(self):
        # Path to reference images
        tick_image_path = './sample button/Finished.png'
        arrow_image_path = './sample button/Unfinished.png'

        # Compare with tick image
        tick_diff = self.compare_images(self.path, tick_image_path)
        print(f"Difference with tick image: {tick_diff}%")

        # Compare with arrow image
        arrow_diff = self.compare_images(self.path, arrow_image_path)
        print(f"Difference with arrow image: {arrow_diff}%")

        # Determine the closest match
        if tick_diff < arrow_diff and tick_diff < 5:  # Set a threshold for detection
            print("Button has a tick ✅")
            return "Finished"
        elif arrow_diff < tick_diff and arrow_diff < 5:
            print("Button has an arrow >>")
            return "Unfinished"
        else:
            print("Unknown button state")
            return "unknown"

    def capture_button_screenshot(self, button:Locator, image_path):
        button.screenshot(path=image_path)


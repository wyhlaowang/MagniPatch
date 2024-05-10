import os
import cv2
from PIL import Image, ImageDraw


class ImagePlotter:
    def __init__(self, image_path):
        self.image_path = image_path
        self.refPt = []
        self.cropping = False
        self.regions = []
        self.image = None
        self.clone = None

    def click_and_crop(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.refPt = [(x, y)]
            self.cropping = True
        elif event == cv2.EVENT_LBUTTONUP:
            self.refPt.append((x, y))
            self.cropping = False
            color = (255, 165, 0) if len(self.regions) < 1 else (255, 255, 0)
            cv2.rectangle(self.image, self.refPt[0], self.refPt[1], color, 2)
            cv2.imshow("Image", self.image)
            if len(self.refPt) == 2:
                self.regions.append((self.refPt[0][0], self.refPt[0][1], self.refPt[1][0], self.refPt[1][1]))

    def setup_image_selection(self):
        self.image = cv2.imread(self.image_path)
        self.clone = self.image.copy()
        cv2.namedWindow("Image")
        cv2.setMouseCallback("Image", self.click_and_crop)
        while len(self.regions) < 2:
            cv2.imshow("Image", self.image)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                self.image = self.clone.copy()
                self.regions.clear()
        cv2.destroyAllWindows()


class ImageCropper:
    def __init__(self, dir_path, regions, out_path):
        self.dir_path = dir_path
        self.regions = regions
        self.out_path = out_path

    def process_image(self, magnifications):
        file_ls = os.listdir(self.dir_path)
        file_ls = [i for i in file_ls if i.endswith(('.png', '.jpg'))]
        for i in file_ls:
            print(self.dir_path+i)
            image = cv2.imread(self.dir_path+i, cv2.IMREAD_COLOR)
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            self.adjust_sizes_and_create_image(pil_image, pil_image.width, pil_image.height, magnifications, file_name=i)

    def adjust_sizes_and_create_image(self, pil_image, original_width, original_height, magnifications, file_name):
        new_sizes = self.calculate_new_sizes(magnifications)
        total_new_width = sum(size[0] for size in new_sizes)
        width_scale = original_width / total_new_width
        adjusted_sizes = [(int(width * width_scale), int(height * width_scale)) for (width, height) in new_sizes]
        new_height = original_height + max(size[1] for size in adjusted_sizes)
        new_image = Image.new("RGB", (original_width, new_height))
        new_image.paste(pil_image, (0, 0))
        self.paste_crops_and_draw_boxes(pil_image, new_image, adjusted_sizes, original_height)

        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)
        new_image.save(self.out_path+file_name)

    def calculate_new_sizes(self, magnifications):
        return [(int((region[2] - region[0]) * mag), int((region[3] - region[1]) * mag)) for region, mag in zip(self.regions, magnifications)]

    def paste_crops_and_draw_boxes(self, pil_image, new_image, adjusted_sizes, original_height):
        current_x = 0
        draw = ImageDraw.Draw(new_image)
        colors = [(255, 165, 0), (255, 255, 0)]
        for (region, size), color in zip(zip(self.regions, adjusted_sizes), colors):
            crop_img = pil_image.crop(region).resize(size, Image.ANTIALIAS)
            new_image.paste(crop_img, (current_x, original_height))
            draw.rectangle([current_x, original_height, current_x + size[0], original_height + size[1]], outline=color, width=12)
            draw.rectangle([region[0], region[1], region[2], region[3]], outline=color, width=4)
            current_x += size[0]


def main(dir_path, roi_image, save_dir='box'):
    plotter = ImagePlotter(dir_path+roi_image) 
    plotter.setup_image_selection()
    magnification1 = float(input("Enter magnification for the first region: "))
    height1, height2 = plotter.regions[0][3] - plotter.regions[0][1], plotter.regions[1][3] - plotter.regions[1][1]
    magnification2 = magnification1 * (height1 / height2)

    cropper = ImageCropper(dir_path, plotter.regions, os.path.join(dir_path, save_dir))
    cropper.process_image([magnification1, magnification2])


if __name__ == "__main__":
    """
    Enlarge images locally.
    * Synchronous processing of multiple images
    * Enlarge two patches simultaneously
    * placement of the magnified area in any corner of the image

    Args:
        dir_path (str): The directory containing the images.
        roi_image (str, optional): The image used to draw RoI.
        save_dir (str, optional): The directory where the enlarged images will be saved. Defaults to "box".
    """
    
    main(dir_path='./data/', roi_image='FLIR_04735ir.png', save_dir='box/')



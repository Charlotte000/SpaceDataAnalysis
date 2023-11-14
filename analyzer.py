import os
from dataclasses import dataclass
from enum import Enum

import cv2
import cv2.typing


class ObjectType(Enum):
    GALAXY = (0, 0, 255)
    STAR = (0, 255, 0)


@dataclass
class Object:
    brightness: float
    position: cv2.typing.Point
    type: ObjectType


class Analyzer:
    @staticmethod
    def crop(img_path: str, folder_path: str, crop_size: tuple[int, int]) -> None:
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        origin = cv2.imread(img_path)
        width, height = origin.shape[1], origin.shape[0]
        for x in range(0, width, crop_size[0]):
            for y in range(0, height, crop_size[1]):
                cropped = origin[y: y + crop_size[1], x: x + crop_size[0]]
                cv2.imwrite(os.path.join(
                    folder_path, f'img{x}x{y}.png'), cropped)

    @staticmethod
    def analyze(img: cv2.typing.MatLike, offset: tuple[int, int], brightness_threshold: float, size: int = 20, blur_amount: int = 41) -> list[Object]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (blur_amount, blur_amount), 0)

        result: list[Object] = []
        value = brightness_threshold
        while value >= brightness_threshold:
            value, point = Analyzer.__detect_brightest(blurred)

            position = (point[0] + offset[0], point[1] + offset[1])
            result.append(
                Object(value, position, ObjectType.STAR if value < 50 else ObjectType.GALAXY))
            cv2.circle(blurred, point, size, (0, 0, 0), -1)

        return result

    @staticmethod
    def draw_overlay(img: cv2.typing.MatLike, objects: list[Object], size: int = 20, alpha: float = .5) -> cv2.typing.MatLike:
        overlay = img.copy()
        for object in objects:
            cv2.circle(overlay, object.position, size, object.type.value, -1)

        return cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    @staticmethod
    def __detect_brightest(img: cv2.typing.MatLike) -> tuple[float, cv2.typing.Point]:
        _, maxVal, _, maxLoc = cv2.minMaxLoc(img)
        return (maxVal, maxLoc)

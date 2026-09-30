import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
import numpy as np


class RoadDetection(Node):

    def __init__(self):
        super().__init__('road_detection')

        self.bridge = CvBridge()

        # Husky RGB kamera topic'ine abone ol
        self.subscription = self.create_subscription(
            Image,
            '/a200_0000/sensors/camera_0/color/image',
            self.image_callback,
            10
        )

        self.get_logger().info(
            'Toprak yol tespiti baslatildi...'
        )


    def image_callback(self, msg):

        # =====================================================
        # 1. ROS2 Image -> OpenCV
        # =====================================================

        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )


        # =====================================================
        # 2. BGR -> HSV
        # =====================================================

        hsv = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2HSV
        )


        # =====================================================
        # 3. TOPRAK RENGINI BELIRLE
        # =====================================================

        # Kahverengi / toprak icin HSV araligi
        lower_brown = np.array([5, 40, 40])
        upper_brown = np.array([30, 255, 255])


        # =====================================================
        # 4. TOPRAK YOL MASKESI
        # =====================================================

        mask = cv2.inRange(
            hsv,
            lower_brown,
            upper_brown
        )


        # =====================================================
        # 5. MORFOLOJIK ISLEMLER
        # =====================================================

        kernel = np.ones(
            (7, 7),
            np.uint8
        )

        # Kucuk gurultuleri temizle
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel
        )

        # Maskedeki kucuk bosluklari kapat
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            kernel
        )


        # =====================================================
        # 6. SADECE TOPRAK YOLU GOSTER
        # =====================================================

        road_area = cv2.bitwise_and(
            frame,
            frame,
            mask=mask
        )


        # =====================================================
        # 7. YURUNEBILIR ALANI MAVI ILE ISARETLE
        # =====================================================

        result = frame.copy()

        # OpenCV BGR kullandigi icin:
        # (255, 0, 0) = MAVI
        blue_overlay = np.zeros_like(frame)
        blue_overlay[:, :] = (255, 0, 0)

        # Mavi rengi sadece yol maskesinin oldugu
        # bolgeye uygula
        colored_road = cv2.bitwise_and(
            blue_overlay,
            blue_overlay,
            mask=mask
        )

        # Kamera goruntusu ile mavi yol katmanini birlestir
        result = cv2.addWeighted(
            result,
            1.0,
            colored_road,
            0.35,
            0
        )


        # =====================================================
        # 8. BILGI YAZISI
        # =====================================================

        cv2.putText(
            result,
            'YURUNEBILIR TOPRAK YOL',
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 0),
            2
        )


        # =====================================================
        # 9. SONUCLARI GOSTER
        # =====================================================

        # Ham kamera goruntusu
        cv2.imshow(
            '1 - Kamera Goruntusu',
            frame
        )

        # Beyaz = yurunebilir toprak
        # Siyah = yurunebilir olarak tespit edilmedi
        cv2.imshow(
            '2 - Toprak Yol Maskesi',
            mask
        )

        # Mavi = robotun yuruyebilecegi alan
        cv2.imshow(
            '3 - Yurunecek Alan (MAVI)',
            result
        )

        cv2.waitKey(1)


def main(args=None):

    rclpy.init(args=args)

    node = RoadDetection()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()

        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
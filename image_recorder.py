import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
import os
import time
import re


class ImageRecorder(Node):

    def __init__(self):
        super().__init__('image_recorder')

        # ROS Image mesajını OpenCV görüntüsüne çevirmek için
        self.bridge = CvBridge()

        # Görüntülerin kaydedileceği klasör
        self.save_dir = os.path.expanduser(
            '~/husky_dataset/images'
        )

        os.makedirs(
            self.save_dir,
            exist_ok=True
        )

        # 2 saniyede 1 görüntü kaydet
        self.save_interval = 2.0

        self.last_save_time = 0.0

        # Klasörde daha önce kaydedilmiş görüntüler varsa
        # son numaradan devam et
        existing_files = [
            f for f in os.listdir(self.save_dir)
            if f.startswith('frame_') and f.endswith('.jpg')
        ]

        numbers = []

        for filename in existing_files:

            match = re.match(
                r'frame_(\d+)\.jpg',
                filename
            )

            if match:
                numbers.append(
                    int(match.group(1))
                )

        if numbers:
            self.image_count = max(numbers)
        else:
            self.image_count = 0

        self.get_logger().info(
            f'Kayıt {self.image_count + 1}. görüntüden devam edecek.'
        )

        # Husky RGB kamera topic'ine abone ol
        self.subscription = self.create_subscription(
            Image,
            '/a200_0000/sensors/camera_0/color/image',
            self.image_callback,
            10
        )

        self.get_logger().info(
            'Görüntü kayıt sistemi çalışıyor...'
        )


    def image_callback(self, msg):

        current_time = time.time()

        # Son kayıttan 2 saniye geçmediyse kaydetme
        if (
            current_time - self.last_save_time
            < self.save_interval
        ):
            return

        try:

            # ROS Image -> OpenCV görüntüsü
            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8'
            )

        except Exception as e:

            self.get_logger().error(
                f'Görüntü alınamadı: {e}'
            )

            return

        # Görüntü numarasını artır
        self.image_count += 1

        # Dosya adını oluştur
        filename = os.path.join(
            self.save_dir,
            f'frame_{self.image_count:04d}.jpg'
        )

        # Görüntüyü kaydet
        success = cv2.imwrite(
            filename,
            frame
        )

        if success:

            self.last_save_time = current_time

            print(
                f'Kaydedildi: {filename}'
            )

        else:

            self.get_logger().error(
                f'Görüntü kaydedilemedi: {filename}'
            )


def main(args=None):

    rclpy.init(args=args)

    node = ImageRecorder()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from cv_bridge import CvBridge

import cv2
import math
from ultralytics import YOLO


class CameraSubscriber(Node):

    def __init__(self):
        super().__init__('camera_subscriber')

        # ROS Image mesajlarını OpenCV görüntüsüne çevirmek için
        self.bridge = CvBridge()

        # Kendi eğittiğimiz YOLOv8 modelini yükle
        self.model = YOLO(
            '/home/yusuf/husky_yolo/runs/'
            'husky_person_chair/weights/best.pt'
        )

        # LiDAR'dan gelen son mesafe
        self.lidar_distance = None

        # DUR mesafesi
        self.stop_distance = 1.0

        # Husky'nin ön tarafında kontrol edeceğimiz açı
        # -10 derece ile +10 derece
        self.lidar_angle = 10.0

        # RGB kamera aboneliği
        self.rgb_subscription = self.create_subscription(
            Image,
            '/a200_0000/sensors/camera_0/color/image',
            self.image_callback,
            10
        )

        # 2D LiDAR aboneliği
        self.lidar_subscription = self.create_subscription(
            LaserScan,
            '/a200_0000/sensors/lidar2d_0/scan',
            self.lidar_callback,
            10
        )

        # DUR komutunu yayınlayacağımız publisher
        self.stop_publisher = self.create_publisher(
            String,
            '/dur_komutu',
            10
        )

        self.get_logger().info(
            'Kamera + özel YOLOv8 + LiDAR + DUR sistemi çalışıyor...'
        )


    def lidar_callback(self, msg):

        # LiDAR açı bilgileri radyan cinsinden gelir
        angle_min = msg.angle_min
        angle_increment = msg.angle_increment

        valid_distances = []

        # Tüm LiDAR ölçümlerini dolaş
        for i, distance in enumerate(msg.ranges):

            # Bu ölçümün açısını hesapla
            angle = angle_min + (i * angle_increment)

            # Radyan -> derece
            angle_degree = math.degrees(angle)

            # Sadece Husky'nin önündeki
            # -10 ile +10 derece arasını kontrol et
            if (
                -self.lidar_angle
                <= angle_degree
                <= self.lidar_angle
            ):

                # Geçerli mesafe mi kontrol et
                if (
                    math.isfinite(distance)
                    and
                    msg.range_min <= distance <= msg.range_max
                ):
                    valid_distances.append(distance)

        # Ön bölgede geçerli ölçüm varsa
        if len(valid_distances) > 0:

            # En yakın engelin mesafesi
            self.lidar_distance = min(
                valid_distances
            )

        else:

            self.lidar_distance = None


    def image_callback(self, msg):

        try:

            # ROS RGB Image -> OpenCV görüntüsü
            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8'
            )

        except Exception as e:

            self.get_logger().error(
                f'RGB görüntüsü alınamadı: {e}'
            )

            return

        # Kendi eğittiğimiz YOLOv8 modeli ile nesne tespiti
        results = self.model(
            frame,
            conf=0.50,
            verbose=False
        )

        # Bounding box çizilmiş görüntü
        annotated_frame = results[0].plot()

        # Görüntüde herhangi bir nesne tespit edildi mi?
        object_detected = False

        # Her tespit için işlem yap
        for box in results[0].boxes:

            object_detected = True

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )

            class_name = self.model.names[
                class_id
            ]

            # LiDAR mesafesi varsa
            if self.lidar_distance is not None:

                print(
                    f'Tespit: {class_name} | '
                    f'Güven: {confidence:.2f} | '
                    f'LiDAR Mesafe: '
                    f'{self.lidar_distance:.2f} m'
                )

            else:

                print(
                    f'Tespit: {class_name} | '
                    f'Güven: {confidence:.2f} | '
                    f'LiDAR Mesafe: okunamadi'
                )

        # ------------------------------------------------
        # DUR KARARI
        # ------------------------------------------------

        # Hem YOLO nesne görüyorsa
        # hem de LiDAR ön tarafta <= 1 metre ölçüyorsa
        if (
            object_detected
            and
            self.lidar_distance is not None
            and
            self.lidar_distance
            <= self.stop_distance
        ):

            msg_stop = String()

            msg_stop.data = 'DUR'

            self.stop_publisher.publish(
                msg_stop
            )

            self.get_logger().warning(
                f'DUR yayınlandı! '
                f'LiDAR mesafesi: '
                f'{self.lidar_distance:.2f} metre'
            )

            # Görüntüye büyük DUR yazısı
            cv2.putText(
                annotated_frame,
                'DUR',
                (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                2,
                (0, 0, 255),
                4
            )

        # ------------------------------------------------
        # LiDAR mesafesini görüntüye yaz
        # ------------------------------------------------

        if self.lidar_distance is not None:

            lidar_text = (
                f'LiDAR: '
                f'{self.lidar_distance:.2f} m'
            )

        else:

            lidar_text = 'LiDAR: ---'

        cv2.putText(
            annotated_frame,
            lidar_text,
            (30, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # Görüntüyü göster
        cv2.imshow(
            'Husky Custom YOLOv8 + LiDAR',
            annotated_frame
        )

        cv2.waitKey(1)


def main(args=None):

    rclpy.init(args=args)

    node = CameraSubscriber()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    node.destroy_node()

    rclpy.shutdown()

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
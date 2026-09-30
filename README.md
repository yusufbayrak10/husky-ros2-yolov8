# Husky ROS2 YOLOv8 Object Detection & Navigation

ROS2, Gazebo ve YOLOv8 kullanılarak Clearpath Husky/A200 mobil robotu üzerinde geliştirilen nesne tespiti, LiDAR tabanlı güvenli hareket kontrolü ve görüntü işleme projesidir.

## Proje Özeti

Bu projede Husky/A200 mobil robotu Gazebo simülasyon ortamında çalıştırılmıştır. Robotun RGB kamerasından alınan görüntüler ROS2 topicleri üzerinden işlenerek YOLOv8 ile gerçek zamanlı person ve chair tespiti gerçekleştirilmiştir.

### Projede gerçekleştirilen işlemler
- ROS2 üzerinden kamera verisinin alınması
- YOLOv8 ile gerçek zamanlı person ve chair tespiti
- Özel veri seti oluşturulması ve YOLOv8 modelinin eğitilmesi
- 2D LiDAR ile mesafe ölçümü
- Nesne algılandığında ve mesafe 1 metre veya altına düştüğünde DUR mesajı yayınlanması
- Klavye ile robot hareket kontrolü
- LiDAR mesafesine göre otomatik yavaşlama ve durma
- HSV ve morfolojik işlemlerle toprak yol tespiti
- Toprak yolun yürünebilir alan olarak maskelenmesi

## Kullanılan Teknolojiler
- Ubuntu 22.04
- ROS2 Humble
- Gazebo / Ignition Fortress
- Clearpath Husky / A200
- Python
- OpenCV
- Ultralytics YOLOv8
- PyTorch
- NumPy
- CvBridge
- 2D LiDAR
- Intel RealSense RGB Kamera
- Roboflow

## YOLOv8 Modeli

Başlangıç modeli olarak YOLOv8 Nano kullanılmış ve özel veri seti üzerinde 50 epoch eğitilmiştir.

Sınıflar: 0 = chair, 1 = person

| Veri Kümesi | Görüntü Sayısı |
|---|---:|
| Train | 85 |
| Validation | 25 |
| Test | 12 |

En iyi eğitilmiş model: `weights/best.pt`

## Model Performansı

| Metrik | Sonuç |
|---|---:|
| Precision | 98.9% |
| Recall | 100% |
| mAP@50 | 99.5% |
| mAP@50-95 | 86.9% |

Sonuçlar 12 görüntülük Gazebo test veri kümesine aittir ve gerçek dünya performansını doğrudan temsil etmez.

## ROS2 Topicleri

RGB Kamera: `/a200_0000/sensors/camera_0/color/image`

2D LiDAR: `/a200_0000/sensors/lidar2d_0/scan`

DUR komutu: `/dur_komutu`

DUR mesaj tipi: `std_msgs/msg/String`

YOLOv8 tarafından nesne algılandığında ve ön LiDAR mesafesi 1 metre veya altına düştüğünde `/dur_komutu` topicine `DUR` mesajı yayınlanır.

## Klavye Kontrolü

- W: İleri
- S: Geri
- A: Sola dön
- D: Sağa dön
- SPACE: Dur
- Q: Programdan çık

| LiDAR Mesafesi | Davranış |
|---|---|
| > 1.0 m | Normal hız |
| 0.5 - 1.0 m | Yavaş hareket |
| <= 0.5 m | Dur |

## Toprak Yol Tespiti

Toprak yol tespitinde görüntü HSV renk uzayına dönüştürülür. Kahverengi alan thresholding ile ayrılır. Morphological Opening küçük gürültüleri temizler, Closing ise maskede oluşan küçük boşlukları kapatır. Sonuçta robotun hareket edebileceği toprak alan maske olarak belirlenir.

HSV aralığı: `lower_brown = [5,40,40]`, `upper_brown = [30,255,255]`

Özel dünya: `road_project/worlds/soil_road.sdf`

Yol tespit kodu: `road_project/road_detection.py`

## Proje Dosyaları

- `camera_subscriber.py` - ROS2 kamera + YOLOv8 + LiDAR + DUR sistemi
- `husky_keyboard_control.py` - Klavye ve LiDAR tabanlı hareket kontrolü
- `image_recorder.py` - Kamera görüntülerini veri seti için kaydeder
- `train.py` - YOLOv8 modelini eğitir
- `test.py` - Model performansını test eder
- `predict.py` - Görüntüler üzerinde tahmin gerçekleştirir
- `weights/best.pt` - Eğitilmiş model ağırlıkları
- `road_project/road_detection.py` - Toprak yol tespiti
- `road_project/worlds/soil_road.sdf` - Özel Gazebo dünyası

## Ana Sistemi Çalıştırma

```bash
source /opt/ros/humble/setup.bash
ros2 launch clearpath_gz simulation.launch.py setup_path:=$HOME/clearpath
```

Yeni terminal:

```bash
cd ~/husky_yolo
source ~/.venv/bin/activate
python3 camera_subscriber.py
```

Klavye kontrolü:

```bash
source /opt/ros/humble/setup.bash
cd ~/husky_yolo
source ~/.venv/bin/activate
python3 husky_keyboard_control.py
```

## Toprak Yol Sistemini Çalıştırma

```bash
source /opt/ros/humble/setup.bash
ros2 launch clearpath_gz simulation.launch.py setup_path:=$HOME/clearpath_road/ world:=soil_road x:=0.0 y:=-10.0 yaw:=1.5708
```

Yeni terminal:

```bash
cd ~/husky_yolo/road_project
source ~/.venv/bin/activate
python3 road_detection.py
```

## Veri Seti

Veri seti Gazebo simülasyonundan alınan görüntüler kullanılarak hazırlanmış, Roboflow üzerinden bounding box etiketlemesi yapılmış ve YOLOv8 formatında dışa aktarılmıştır.

## Not

Proje simülasyon ortamında geliştirilmiştir. Gerçek robot ve gerçek dünya ortamlarında kullanılmadan önce daha çeşitli verilerle test ve doğrulama yapılması gerekir.

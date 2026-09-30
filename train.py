from ultralytics import YOLO


def main():

    # Önceden eğitilmiş YOLOv8 Nano modelini yükle
    model = YOLO("yolov8n.pt")

    # Kendi Husky veri setimiz ile modeli eğit
    model.train(
        data="/home/yusuf/husky_yolo/dataset/data.yaml",

        # Eğitim ayarları
        epochs=50,
        imgsz=640,
        batch=16,

        # NVIDIA GPU kullan
        device=0,

        # Sonuçların kaydedileceği klasör
        project="/home/yusuf/husky_yolo/runs",
        name="husky_person_chair"
    )


if __name__ == "__main__":
    main()
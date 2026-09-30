from ultralytics import YOLO


def main():

    # Eğitim sonucunda elde edilen en iyi modeli yükle
    model = YOLO(
        "/home/yusuf/husky_yolo/runs/"
        "husky_person_chair/weights/best.pt"
    )

    # Test görüntüleri üzerinde nesne tespiti yap
    model.predict(
        source="/home/yusuf/husky_yolo/dataset/test/images",

        # Görüntü boyutu
        imgsz=640,

        # Minimum güven skoru
        conf=0.50,

        # NVIDIA GPU
        device=0,

        # Bounding box çizilmiş görüntüleri kaydet
        save=True,

        # Güven skorlarını da göster/kaydet
        save_conf=True,

        # Sonuçların kaydedileceği klasör
        project="/home/yusuf/husky_yolo/runs",
        name="test_predictions"
    )


if __name__ == "__main__":
    main()
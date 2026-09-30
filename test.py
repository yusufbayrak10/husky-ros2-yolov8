from ultralytics import YOLO


def main():

    # Eğitim sonucunda elde edilen en iyi modeli yükle
    model = YOLO(
        "/home/yusuf/husky_yolo/runs/"
        "husky_person_chair/weights/best.pt"
    )

    # Modeli daha önce eğitimde kullanılmamış
    # TEST veri seti üzerinde değerlendir
    results = model.val(
        data="/home/yusuf/husky_yolo/dataset/data.yaml",
        split="test",
        imgsz=640,
        device=0
    )

    # Test sonuçlarını terminale yazdır
    print(results)


if __name__ == "__main__":
    main()
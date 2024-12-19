import cv2
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("No se pudo capturar el frame")
        break

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar los recursos
cap.release()
cv2.destroyAllWindows()

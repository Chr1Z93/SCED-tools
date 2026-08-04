from pathlib import Path
from PIL import Image

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import (
    QPixmap,
    QImage,
    QPainter,
    QColor,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
)

import sys

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

CROP_WIDTH = 1479
CROP_HEIGHT = 2064
OUTPUT_WIDTH = 632
OUTPUT_HEIGHT = 882
OUTPUT_FOLDER = "cropped"

# ------------------------------------------------------------


class CropWidget(QWidget):
    current_image_changed = Signal(str, int, int, float)

    def __init__(self):
        super().__init__()

        self.images = []
        self.index = 0
        self.image = None
        self.preview_image = None
        self.pixmap = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.rotation = 0.0
        self.dragging = False
        self.last_mouse = None

        self.setMinimumSize(900, 1200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def load_folder(self, folder):
        self.images = sorted(
            [
                p
                for p in Path(folder).rglob("*")
                if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
            ]
        )

        self.index = 0
        self.load_current()

    def load_current(self):
        if not self.images:
            return

        self.image = Image.open(self.images[self.index]).convert("RGBA")

        self.pixmap = QPixmap.fromImage(
            QImage(
                self.image.tobytes(),
                self.image.width,
                self.image.height,
                QImage.Format.Format_RGBA8888,
            )
        )
        self.offset_x = 0
        self.offset_y = 0
        self.rotation = 0.0
        self.update_preview()
        self.update()
        self.current_image_changed.emit(
            self.images[self.index].name,
            self.index + 1,
            len(self.images),
            self.rotation,
        )

    def update_preview(self):
        if self.image is None:
            return

        rotated = self.image.rotate(
            self.rotation,
            expand=True,
            resample=Image.Resampling.BICUBIC,
        )

        self.pixmap = QPixmap.fromImage(
            QImage(
                rotated.tobytes(),
                rotated.width,
                rotated.height,
                QImage.Format.Format_RGBA8888,
            )
        )

        self.preview_image = rotated
        self.scale = min(
            self.width() / rotated.width,
            self.height() / rotated.height,
        )

    def crop_rect_screen(self):
        width = CROP_WIDTH * self.scale
        height = CROP_HEIGHT * self.scale

        return QRectF(
            self.width() / 2 - width / 2,
            self.height() / 2 - height / 2,
            width,
            height,
        )

    def get_crop_box(self):
        if self.pixmap is None:
            return

        rect = self.crop_rect_screen()

        image_x = (
            rect.x()
            - (self.width() / 2 + self.offset_x - self.pixmap.width() * self.scale / 2)
        ) / self.scale

        image_y = (
            rect.y()
            - (
                self.height() / 2
                + self.offset_y
                - self.pixmap.height() * self.scale / 2
            )
        ) / self.scale

        return (
            int(image_x),
            int(image_y),
            int(image_x + CROP_WIDTH),
            int(image_y + CROP_HEIGHT),
        )

    def save_current(self):
        if self.preview_image is None:
            return

        crop = self.get_crop_box()
        if crop is None:
            return

        result = self.preview_image.crop(crop)
        result = result.resize(
            (OUTPUT_WIDTH, OUTPUT_HEIGHT),
            Image.Resampling.LANCZOS,
        )
        result = result.convert("RGB")

        output = self.images[self.index].parent / OUTPUT_FOLDER
        output.mkdir(exist_ok=True)
        output_file = output / f"{self.images[self.index].stem}.webp"

        result.save(
            output_file,
            "WEBP",
            quality=95,
            method=6,
        )

        print("Saved:", output_file)

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.fillRect(self.rect(), QColor(40, 40, 40))

        if self.pixmap:
            painter.save()
            painter.translate(
                self.width() / 2 + self.offset_x,
                self.height() / 2 + self.offset_y,
            )
            painter.scale(self.scale, self.scale)
            painter.drawPixmap(
                -self.pixmap.width() // 2,
                -self.pixmap.height() // 2,
                self.pixmap,
            )

            painter.restore()

        painter.setPen(QPen(QColor(255, 0, 0), 3))
        painter.drawRect(self.crop_rect_screen())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_mouse = event.position()

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.position() - self.last_mouse
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_mouse = event.position()

            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def keyPressEvent(self, event):

        move_step = 10 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
        rot_step = 1 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 0.1

        if event.key() == Qt.Key.Key_Left:
            self.offset_x -= move_step

        elif event.key() == Qt.Key.Key_Right:
            self.offset_x += move_step

        elif event.key() == Qt.Key.Key_Up:
            self.offset_y -= move_step

        elif event.key() == Qt.Key.Key_Down:
            self.offset_y += move_step

        elif event.key() == Qt.Key.Key_Q:
            self.rotation += rot_step
            self.update_preview()
            self.emit_status()

        elif event.key() == Qt.Key.Key_E:
            self.rotation -= rot_step
            self.update_preview()
            self.emit_status()

        elif event.key() == Qt.Key.Key_Return:
            self.save_current()
            self.next_image()

        elif event.key() == Qt.Key.Key_Escape:
            self.next_image()

        self.update()

    def emit_status(self):
        if not self.images:
            return

        self.current_image_changed.emit(
            self.images[self.index].name,
            self.index + 1,
            len(self.images),
            self.rotation,
        )

    def next_image(self):
        self.index += 1

        if self.index < len(self.images):
            self.load_current()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.status_label = QLabel("No folder loaded")
        self.cropper = CropWidget()
        self.cropper.current_image_changed.connect(self.update_status)

        button = QPushButton("Open folder")
        button.clicked.connect(self.open_folder)
        label = QLabel(
            "Enter: Save | Esc: Skip | Arrow keys: Move | Q/E: Rotate | Shift: 10x moving / rotating"
        )
        layout = QVBoxLayout()

        layout.addWidget(button)
        layout.addWidget(self.status_label)
        layout.addWidget(label)
        layout.addWidget(self.cropper)

        self.setLayout(layout)

    def update_status(self, filename, index, total, rotation):
        self.status_label.setText(
            f"{index}/{total}: {filename} | Rotation: {rotation:+.1f}°"
        )
        self.setWindowTitle(f"Card Cropper ({index}/{total})")

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory()

        if folder:
            self.cropper.load_folder(folder)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

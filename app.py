"""連番PNGをまとめてPDFにするPySide6アプリ。"""
import os
import re
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QSizeF, QRectF, QMarginsF, QThread, Signal, QEvent
from PySide6.QtGui import QImageReader, QPixmap, QPainter, QPdfWriter, QPageSize, QPageLayout, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox, QListWidget,
    QListWidgetItem, QAbstractItemView, QLabel, QPushButton, QComboBox,
    QSpinBox, QHBoxLayout, QVBoxLayout, QSplitter, QProgressBar, QSizePolicy,
)

STYLE = '''
QMainWindow, QMessageBox { background: #fff9f5; }
QWidget { color: #493d39; font-family: "Yu Gothic UI"; font-size: 13px; }
QLabel { background: transparent; }
QPushButton { background: #ffffff; border: 1px solid #f0e2da;
    border-radius: 13px; padding: 10px 14px; font-weight: 600; }
QPushButton:hover { background: #fce5e2; border-color: #e4aaa9; }
QPushButton:pressed { background: #f3d0cc; }
QPushButton:disabled { color: #bdaea8; background: #f5eeea; }
QPushButton#save { background: #d56670; border: 0; color: white; padding: 12px 30px; }
QPushButton#save:hover { background: #c25460; }
QPushButton#save:disabled { background: #e9c4c3; color: #fff9f5; }
QListWidget { background: white; border: 1px solid #f0e5de; border-radius: 18px;
    padding: 12px; alternate-background-color: #fffaf7; outline: 0; }
QListWidget::item { border-radius: 9px; padding: 10px; }
QListWidget::item:selected { background: #fae2df; color: #a74755; }
QListWidget::item:hover { background: #fff0e6; }
QComboBox, QSpinBox { background: white; border: 1px solid #eeddd6;
    border-radius: 12px; padding: 9px 12px; min-height: 20px; }
QComboBox QAbstractItemView { background: white; selection-background-color: #fae2df; }
QSplitter::handle { background: transparent; width: 16px; }
QStatusBar { color: #94817a; background: #fff9f5; }
QProgressBar { background: #f9e8df; border: 0; border-radius: 6px; text-align: center; }
QProgressBar::chunk { background: #d56670; border-radius: 6px; }
'''


def natural_key(path):
    return tuple((0, int(p)) if p.isdigit() else (1, p.casefold())
                 for p in re.split(r"(\d+)", Path(path).name))


def collect_pngs(paths):
    found = []
    for value in paths:
        path = Path(value)
        if path.is_dir():
            found.extend(p for p in path.iterdir() if p.is_file() and p.suffix.lower() == '.png')
        elif path.is_file() and path.suffix.lower() == '.png':
            found.append(path)
    return sorted(found, key=lambda p: (natural_key(p), str(p).casefold()))


def export_pdf(paths, destination, paper='image', dpi=300, progress=None):
    """一枚ずつ読み込み、完了時のみ保存先を置き換える。"""
    if not paths:
        raise ValueError('PNGを追加してください。')
    target = Path(destination)
    handle, temporary = tempfile.mkstemp(prefix='.png_pdf_', suffix='.pdf', dir=target.parent)
    os.close(handle)
    painter = QPainter()
    writer = None
    try:
        writer = QPdfWriter(temporary)
        writer.setResolution(dpi)
        writer.setTitle(target.stem)
        writer.setCreator('PNG to PDF')
        for index, path in enumerate(paths):
            reader = QImageReader(str(path))
            reader.setAutoTransform(True)
            image = reader.read()
            if image.isNull():
                raise ValueError(f'画像を読み込めません: {Path(path).name}\n{reader.errorString()}')
            if paper == 'a4':
                page = QPageSize(QPageSize.PageSizeId.A4)
            else:
                page = QPageSize(QSizeF(image.width() * 25.4 / dpi,
                                       image.height() * 25.4 / dpi),
                                 QPageSize.Unit.Millimeter, 'Image',
                                 QPageSize.SizeMatchPolicy.ExactMatch)
            layout = QPageLayout(page, QPageLayout.Orientation.Portrait,
                                 QMarginsF(0, 0, 0, 0))
            if not writer.setPageLayout(layout):
                raise ValueError(f'ページサイズを設定できません: {Path(path).name}')
            if index == 0:
                if not painter.begin(writer):
                    raise OSError('PDFの書き込みを開始できません。')
                painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering, True)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            elif not writer.newPage():
                raise OSError('PDFにページを追加できません。')
            bounds = QRectF(0, 0, writer.width(), writer.height())
            painter.fillRect(bounds, Qt.GlobalColor.white)
            fitted = QSizeF(image.size())
            fitted.scale(bounds.size(), Qt.AspectRatioMode.KeepAspectRatio)
            rect = QRectF((bounds.width() - fitted.width()) / 2,
                          (bounds.height() - fitted.height()) / 2,
                          fitted.width(), fitted.height())
            painter.drawImage(rect, image)
            if progress:
                progress(index + 1)
        if not painter.end():
            raise OSError('PDFの書き込みを完了できません。')
        writer = None
        os.replace(temporary, target)
    finally:
        if painter.isActive():
            painter.end()
        writer = None
        if os.path.exists(temporary):
            os.unlink(temporary)


class ExportThread(QThread):
    progress = Signal(int)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, paths, destination, paper, dpi, parent):
        super().__init__(parent)
        self.args = paths, destination, paper, dpi

    def run(self):
        try:
            export_pdf(*self.args, progress=self.progress.emit)
            self.succeeded.emit(self.args[1])
        except Exception as exc:
            self.failed.emit(str(exc))


class ImageList(QListWidget):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setAlternatingRowColors(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            self.files_dropped.emit([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PNG → PDF')
        self.resize(960, 720)
        self.setMinimumSize(680, 460)
        self.setStyleSheet(STYLE)
        self.worker = None
        self.preview_pixmap = QPixmap()
        self.last_directory = str(Path.home())
        self.body = QWidget()
        self.setCentralWidget(self.body)
        root = QVBoxLayout(self.body)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)
        eyebrow = QLabel('PNG TO PDF')
        eyebrow.setStyleSheet('color: #be646d; font-size: 12px; font-weight: 700;')
        root.addWidget(eyebrow)
        title = QLabel('PNGをひとつのPDFに')
        title.setStyleSheet('font-size: 30px; font-weight: 700;')
        root.addWidget(title)
        root.addWidget(QLabel('PNGやフォルダーを一覧へドロップ。ドラッグでページ順を変更できます。'))
        toolbar_card = QWidget()
        toolbar_card.setObjectName('toolbar')
        toolbar_card.setStyleSheet('QWidget#toolbar { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fff0dc,stop:1 #fde3e6); border-radius: 18px; }')
        toolbar = QHBoxLayout(toolbar_card)
        toolbar.setContentsMargins(16, 16, 16, 16)
        for text, callback in [('PNGを追加', self.add_files), ('フォルダーを追加', self.add_folder),
                               ('数字順に整列', self.sort_items), ('選択を削除', self.remove_items),
                               ('クリア', self.clear_items)]:
            button = QPushButton(text)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        root.addWidget(toolbar_card)
        self.images = ImageList()
        self.images.files_dropped.connect(self.add_paths)
        self.images.currentItemChanged.connect(self.update_preview)
        self.images.model().rowsMoved.connect(self.update_count)
        self.preview = QLabel('ここにプレビューが表示されます')
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(200, 200)
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.preview.installEventFilter(self)
        self.preview.setStyleSheet('background: #ffffff; border: 1px solid #f0e5de; border-radius: 18px; color: #94817a;')
        self.preview.setScaledContents(False)
        split = QSplitter()
        split.addWidget(self.images)
        split.addWidget(self.preview)
        split.setSizes([420, 390])
        root.addWidget(split, 1)
        self.count = QLabel('0ページ')
        root.addWidget(self.count)
        options = QHBoxLayout()
        options.addWidget(QLabel('ページサイズ'))
        self.paper = QComboBox()
        self.paper.addItem('画像に合わせる', 'image')
        self.paper.addItem('A4（縦・余白は白）', 'a4')
        options.addWidget(self.paper)
        options.addWidget(QLabel('画像の基準DPI'))
        self.dpi = QSpinBox()
        self.dpi.setRange(36, 1200)
        self.dpi.setValue(300)
        self.dpi.setToolTip('画像サイズに合わせる場合の印刷サイズを決めます。画素数は減らしません。')
        options.addWidget(self.dpi)
        options.addStretch()
        self.save = QPushButton('PDFに保存')
        self.save.setObjectName('save')
        self.save.clicked.connect(self.save_pdf)
        self.save.setEnabled(False)
        options.addWidget(self.save)
        root.addLayout(options)
        self.progress = QProgressBar()
        self.progress.hide()
        root.addWidget(self.progress)
        self.statusBar().showMessage('透明な部分は白い背景で保存します。')

    def paths(self):
        return [self.images.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.images.count())]

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'PNGを選択', self.last_directory, 'PNG画像 (*.png *.PNG)')
        self.add_paths(paths)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'PNGのあるフォルダー', self.last_directory)
        if folder:
            self.add_paths([folder])

    def add_paths(self, values):
        existing = {os.path.normcase(os.path.abspath(p)) for p in self.paths()}
        try:
            paths = collect_pngs(values)
        except OSError as exc:
            QMessageBox.warning(self, '追加できません', str(exc))
            return
        for path in paths:
            full = str(path.resolve())
            key = os.path.normcase(full)
            if key in existing:
                continue
            item = QListWidgetItem(path.name)
            item.setData(Qt.ItemDataRole.UserRole, full)
            item.setToolTip(full)
            self.images.addItem(item)
            existing.add(key)
        if paths:
            self.last_directory = str(paths[0].parent)
        if self.images.currentRow() < 0 and self.images.count():
            self.images.setCurrentRow(0)
        self.update_count()

    def sort_items(self):
        items = [self.images.takeItem(0) for _ in range(self.images.count())]
        for item in sorted(items, key=lambda i: natural_key(i.data(Qt.ItemDataRole.UserRole))):
            self.images.addItem(item)
        if items:
            self.images.setCurrentRow(0)

    def remove_items(self):
        for item in self.images.selectedItems():
            self.images.takeItem(self.images.row(item))
        self.update_count()

    def clear_items(self):
        self.images.clear()
        self.update_count()

    def update_count(self, *args):
        self.count.setText(f'{self.images.count()}ページ · 一覧の上から順に保存')
        self.save.setEnabled(self.images.count() > 0)

    def update_preview(self, current, previous=None):
        self.preview_pixmap = QPixmap()
        if current:
            reader = QImageReader(current.data(Qt.ItemDataRole.UserRole))
            reader.setAutoTransform(True)
            size = reader.size()
            if size.isValid():
                size.scale(QSize(1200, 1200), Qt.AspectRatioMode.KeepAspectRatio)
                reader.setScaledSize(size)
            self.preview_pixmap = QPixmap.fromImage(reader.read())
        self.fit_preview()

    def fit_preview(self):
        if self.preview_pixmap.isNull():
            self.preview.setText('プレビューなし')
        else:
            self.preview.setPixmap(self.preview_pixmap.scaled(
                self.preview.size() - QSize(20, 20), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_preview()

    def eventFilter(self, watched, event):
        if watched is self.preview and event.type() == QEvent.Type.Resize:
            self.fit_preview()
        return super().eventFilter(watched, event)

    def save_pdf(self):
        paths = self.paths()
        if not paths:
            return
        proposed = str(Path(paths[0]).parent / (Path(paths[0]).parent.name + '.pdf'))
        destination, _ = QFileDialog.getSaveFileName(self, 'PDFを保存', proposed, 'PDF (*.pdf)')
        if not destination:
            return
        if not destination.lower().endswith('.pdf'):
            destination += '.pdf'
            if Path(destination).exists() and QMessageBox.question(
                    self, '上書き確認', f'{Path(destination).name} を上書きしますか？') != QMessageBox.StandardButton.Yes:
                return
        self.body.setEnabled(False)
        self.progress.setRange(0, len(paths))
        self.progress.setValue(0)
        self.progress.show()
        self.statusBar().showMessage('PDFを作成しています…')
        self.worker = ExportThread(paths, destination, self.paper.currentData(), self.dpi.value(), self)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.succeeded.connect(self.export_succeeded)
        self.worker.failed.connect(lambda message: QMessageBox.critical(self, '保存できません', message))
        self.worker.finished.connect(self.export_finished)
        self.worker.start()

    def export_succeeded(self, path):
        self.statusBar().showMessage(f'保存しました: {path}')
        QMessageBox.information(self, '保存完了', f'PDFを保存しました。\n\n{path}')

    def export_finished(self):
        self.body.setEnabled(True)
        self.progress.hide()
        self.worker.deleteLater()
        self.worker = None
        self.statusBar().showMessage('保存処理が完了しました。')

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            event.ignore()
            self.statusBar().showMessage('PDFの保存が終わってから閉じてください。')
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Yu Gothic UI', 10))
    window = Window()
    if len(sys.argv) > 1:
        window.add_paths(sys.argv[1:])
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

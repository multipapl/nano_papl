# QFluentWidgets Survival Guide

> **Мета**: Зібрати найпоширеніші пастки, помилки та best practices при роботі з QFluentWidgets.

---

## 🎨 Native Theming (КРИТИЧНО!)

### Основна філософія

QFluentWidgets **не фарбує** стандартні `QWidget` автоматично. Використання `setStyleSheet("background: #hex")` для структурних блоків — це **антипатерн**, який:
- ❌ Ламає спадковість теми
- ❌ Вимагає ручного керування кольорами
- ❌ Конфліктує з HiDPI масштабуванням
- ❌ Не реагує на зміну теми

### ✅ Правильний підхід: Native paintEvent

Використовуємо `paintEvent` + `QPainter` — той самий механізм, що й у внутрішніх компонентах бібліотеки.

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt
from qfluentwidgets import isDarkTheme, qconfig

class ThemeAwareBackground(QWidget):
    """Віджет з нативною підтримкою теми"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Fluent Design кольори
        self.light_bg = QColor("#ffffff")
        self.dark_bg = QColor("#272727")
        # Автоматично перемальовуємо при зміні теми
        qconfig.themeChanged.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.dark_bg if isDarkTheme() else self.light_bg)
        painter.drawRect(self.rect())
```

**Використання:**
```python
# ❌ Старий спосіб
background = QWidget()
background.setStyleSheet("background: #2d2d2d;")

# ✅ Правильний спосіб
background = ThemeAwareBackground()
```

**Чому це краще:**
- ✅ **Продуктивність**: QPainter малює миттєво, CSS-двигун Qt важкий
- ✅ **Надійність**: Немає конфліктів з border-radius батьківських елементів  
- ✅ **Чистота**: Логіка відділена від стилів
- ✅ **Автоматичність**: Підписка на `qconfig.themeChanged` - оновлення безкоштовно

### QSplitter Handle Styling

Для роздільників (QSplitter) можна використовувати CSS, але з динамічними кольорами:

```python
def _apply_splitter_style(self):
    dark = isDarkTheme()
    handle_bg = "#3a3a3a" if dark else "#e0e0e0"
    
    self.splitter.setStyleSheet(f"""
        QSplitter::handle {{
            background-color: {handle_bg};
            width: 1px;
        }}
        QSplitter::handle:hover {{
            background-color: #0078d4;
        }}
    """)

# Підключити до теми
qconfig.themeChanged.connect(self._apply_splitter_style)
```

---

## 🚫 Типові помилки

### 1. setStyleSheet для позиціонування

## Філософія бібліотеки

QFluentWidgets — "золота клітка": дає топовий Windows 11 style з коробки, але вимагає дотримання правил. Крок вліво-вправо → артефакти, поламані анімації, краші.

**Підхід**: Сприймай як роботу з нодами — не ламай пайплайн кастомними хаками.

---

## 1. ❌ Забудь про `setStyleSheet` (майже повністю)

### Проблема
Fluent віджети малюються через `paintEvent` з складною системою палітр. `setStyleSheet` ламає:
- Закруглення (border-radius)
- Тіні (drop shadows)
- Анімації (ripple effects)
- Темну тему

### ✅ Рішення

**Для зміни кольорів:**
```python
# Замість setStyleSheet
widget.setTextColor(QColor("#fff"))
widget.setCheckColor(QColor("#0078d4"))
```

**Для кастомного фону:**
```python
# Загорни в QFrame, стилізуй фрейм
frame = QFrame()
frame.setStyleSheet("background: #f0f0f0; border-radius: 8px;")

# Fluent віджет всередину з прозорим фоном
fluent_widget.setAttribute(Qt.WA_TranslucentBackground)
layout.addWidget(fluent_widget)
```

**Для глобальних кольорів:**
```python
from qfluentwidgets import qconfig, themeColor

accent_color = themeColor()  # Поточний accent color теми
```

---

## 2. 🖥️ High DPI та пікселі

### Проблема
Хардкод розмірів (`setFixedHeight(60)`, `AVATAR_SIZE = 32`) на 4K з масштабуванням 150-200% виглядає мікроскопічно.

### ✅ Рішення

```python
# ❌ НЕ ТАК
widget.setFixedSize(300, 200)

# ✅ ТАК
widget.setMinimumSize(300, 200)  # Мінімальний розмір
widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

# Або покладайся на sizeHint
# QFluentWidgets має хороші дефолтні розміри
```

**Для шрифтів:**
```python
# Використовуй pt, не px
font.setPointSize(10)  # Масштабується автоматично
# Не font.setPixelSize(14)
```

---

## 3. 📦 Використовуй CardWidget для структури

### Проблема
Просто `QVBoxLayout` виглядає непрофесійно, проблеми з відступами.

### ✅ Рішення

```python
from qfluentwidgets import SettingCardGroup, SimpleCardWidget, CardWidget

# Для налаштувань
group = SettingCardGroup("Title", parent)
group.addSettingCard(card1)
group.addSettingCard(card2)

# Для кастомних блоків
card = SimpleCardWidget(parent)
card_layout = QVBoxLayout(card)
card_layout.addWidget(your_content)
# Автоматичні тіні та бордери ✓
```

---

## 4. 💬 InfoBar та StateToolTip замість print()

### Фіча бібліотеки
Найкраща частина QFluentWidgets — системи нотифікацій.

```python
from qfluentwidgets import InfoBar, InfoBarPosition, StateToolTip

# Успіх/Помилка
InfoBar.success(
    title="Success",
    content="Operation completed",
    parent=self,
    duration=2000,
    position=InfoBarPosition.TOP
)

InfoBar.error(
    title="Error",
    content="API request failed",
    parent=self,
    duration=3000
)

# Процес (не блокує UI)
self.state_tooltip = StateToolTip("Generating", "Please wait...", self)
self.state_tooltip.move(self.state_tooltip.getSuitablePos())
self.state_tooltip.show()

# Після завершення
self.state_tooltip.setContent("Done!")
self.state_tooltip.setState(True)
QTimer.singleShot(1000, self.state_tooltip.close)
```

---

## 5. 🎨 Правильна обробка теми

### ✅ Паттерн

```python
from qfluentwidgets import isDarkTheme, qconfig

class CustomWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Підписуємось на зміну теми
        qconfig.themeChanged.connect(self.update_style)
        
        # 2. Застосовуємо стиль одразу
        self.update_style()
    
    def update_style(self):
        """Оновлює кольори залежно від поточної теми"""
        is_dark = isDarkTheme()
        
        bg = "#2d2d2d" if is_dark else "#f5f5f5"
        text = "#ffffff" if is_dark else "#000000"
        
        # Оновлюємо тільки коли треба
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {text};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
```

**Важливо**: 
- Завжди підключайся до `qconfig.themeChanged`
- Не малюй в `paintEvent` без потреби
- Використовуй `isDarkTheme()` замість власних флагів

---

## 6. ⚡ Асинхронність обов'язкова

### Проблема
QFluentWidgets має багато анімацій. Блокування потоку на 0.1 сек → фріз анімацій → дешевий вигляд.

### ✅ Правило
**Ніякої важкої логіки в UI потоці!**

```python
# ❌ НЕ ТАК
def on_button_click(self):
    data = heavy_computation()  # UI freeze
    self.update_ui(data)

# ✅ ТАК
def on_button_click(self):
    self.worker = Worker()
    self.worker.finished.connect(self.update_ui)
    self.worker.start()
```

**Що виносити в Worker:**
- API запити
- Читання/запис файлів
- Парсинг JSON/XML
- Обробка зображень
- Будь-які операції > 50ms

---

## 7. 🔧 Common Pitfalls (Типові підводні камені)

### Font Size Warnings
```python
# ❌ Викликає QFont::setPointSize warning
widget.setStyleSheet("font-size: 0pt;")
widget.setStyleSheet("font-size: -1px;")
widget.setStyleSheet("font-size: 14px;")  # Особливо під час init/анімацій!

# ✅ Вірно - використовуй QFont API
font = widget.font()
font.setPixelSize(14)  # Або setPointSize(10)
widget.setFont(font)
# CSS тільки для кольорів, margins, padding
widget.setStyleSheet("color: #333; padding: 5px;")
```

**Чому це критично**: Під час ініціалізації віджетів або анімацій Qt намагається конвертувати px→pt, але віджет ще має розмір 0x0. Формула ділить на 0 → pointSize = -1 → warning spam.

**Рішення**: НІКОЛИ не вказуй `font-size` в `setStyleSheet` для QFluentWidgets. Завжди через `QFont`.

### Suppressing Library Warnings

Якщо warnings все ще з'являються з **внутрішніх компонентів QFluentWidgets** (NavigationBar, SettingCard) - це проблема бібліотеки, не твого коду.

**Рішення**: Додай Qt message handler в `main.py`:

```python
from PySide6.QtCore import QtMsgType, qInstallMessageHandler

def qt_message_handler(mode, context, message):
    # Suppress QFont warnings from QFluentWidgets internals
    if "QFont::setPointSize: Point size <= 0" in message:
        return  # Silently ignore
    
    # Pass through other messages
    if mode == QtMsgType.QtWarningMsg:
        print(f"Warning: {message}")

# Install BEFORE QApplication
qInstallMessageHandler(qt_message_handler)
app = QApplication(sys.argv)
```

Це не "маскування проблеми" - це єдиний спосіб боротьби з багами third-party бібліотек.

### Ламаються скролли
```python
# ❌ setStyleSheet на ScrollArea
scroll.setStyleSheet("background: white;")

# ✅ Стилізуй віджет всередині, не ScrollArea
scroll.setWidgetResizable(True)
scroll.widget().setStyleSheet("background: white;")
```

### Іконки не показуються
```python
# ❌ Передаєш None як іконку
btn = PrimaryPushButton(None, "Text")

# ✅ Або іконка, або без неї
btn = PrimaryPushButton("Text", parent)  # Без іконки
btn = PrimaryPushButton(FluentIcon.ADD, "Text", parent)  # З іконкою
```

---


## 8. 🧩 Patterns & Recipes

### Sticky Buttons & Menus
```python
# ❌ ToolButton з setMenu часто "залипає" в pressed стані
btn = ToolButton(self)
btn.setMenu(menu)
btn.setPopupMode(ToolButton.InstantPopup)

# ✅ Рішення: TransparentPushButton + Manual Menu
btn = TransparentPushButton("Text", self, icon)
btn.clicked.connect(lambda: _show_menu(btn, menu))

def _show_menu(btn, menu):
    # Ручне позиціонування
    pos = btn.mapToGlobal(QPoint(0, btn.height() + 4))
    menu.exec(pos)
```

### Custom "Chip" Buttons
Якщо потрібен стиль "Tags/Chips" (овальні кнопки з фоном):
1. Використовуй `TransparentPushButton` (має прозорий фон базово).
2. Додай `border-radius` і `background-color` через `setStyleSheet`.
3. **Важливо**: Шрифт задавай через `setFont`, а не CSS.
4. Прибери `menu-indicator` в CSS якщо використовуєш меню.

```python
# Python
font = btn.font()
font.setPixelSize(12)
btn.setFont(font)

# CSS (в _on_theme_changed)
"""
TransparentPushButton {
    background-color: rgba(0,0,0,0.05);
    border-radius: 14px;
    padding: 4px 12px;
}
TransparentPushButton::menu-indicator {
    image: none;
}
"""
```

## 9. 📋 Quick Reference

### Основні компоненти

| Компонент | Використання |
|-----------|--------------|
| `CardWidget` | Базовий контейнер з тінню |
| `SimpleCardWidget` | Спрощена картка |
| `SettingCardGroup` | Група налаштувань |
| `SwitchSettingCard` | Налаштування з перемикачем |
| `InfoBar` | Нотифікації |
| `StateToolTip` | Індикатор процесу |
| `FluentWindow` | Головне вікно з навігацією |

### Корисні утиліти

```python
from qfluentwidgets import (
    isDarkTheme,      # Перевірка теми
    themeColor,       # Accent color
    setTheme,         # Зміна теми
    qconfig,          # Глобальна конфігурація
    Theme             # Enum: LIGHT, DARK, AUTO
)
```

---

## 💡 Best Practices Summary

1. ✅ Використовуй нативні компоненти бібліотеки
2. ✅ Підписуйся на `qconfig.themeChanged`
3. ✅ Уникай `setStyleSheet` де можливо
4. ✅ Використовуй `setMinimumSize` замість `setFixedSize`
5. ✅ Виноси важку логіку в QThread/Worker
6. ✅ Використовуй InfoBar для feedback
7. ✅ Групуй UI в CardWidget
8. ✅ Шрифти в `pt`, не `px`

---

## 🚫 Never Do This

```python
# ❌ Хардкод кольорів без реакції на тему
widget.setStyleSheet("background: #ffffff;")

# ❌ Фіксовані розміри в пікселях
widget.setFixedSize(300, 200)

# ❌ Важка логіка в UI потоці
data = requests.get(url).json()

# ❌ setStyleSheet на Fluent віджети
PrimaryPushButton.setStyleSheet("background: red;")

# ❌ Ігнорування themeChanged сигналу
# (твій UI буде ламатися при перемиканні теми)
```

---

**Золоте правило**: Якщо щось виглядає складно — бібліотека вже має для цього компонент. Шукай в документації замість костилів.

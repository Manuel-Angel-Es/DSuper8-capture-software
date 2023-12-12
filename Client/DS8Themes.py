"""
Proyecto DSuper8 basado en rpi-film-capture de Joe Herman.

Software modificado por Manuel Ángel.

Traducido al castellano por Manuel Ángel.

Interfaz de usuario rediseñada y traducida al castellano por Manuel Ángel.

DSThemes.py: Archivo de temas para la GUI.

Última versión: 20231130.
"""

darkTheme = '''
/* Dialog background color */ 
QDialog {
    background: solid #282828;        
}

/* Tab widget frame style */
QTabWidget::pane {    
    border-top: none;
    background: solid #323232;
}

/* Tab bar style */
QTabWidget::tab-bar {
    alignment: center;
}

/* Tab style */
QTabBar::tab {
    background: solid #464646;
    border: 2px solid #969696;
    border-bottom-color: #C2C7CB;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #808080;
    min-width: 8ex;
    padding: 5px;
}

/* Selected tab style */
QTabBar::tab:selected {
    background: solid #323232;
    border-color: #6e6e6e;    
    border-bottom: none;
    color: #d2d2d2;
}

/* Not selected tab style */
QTabBar::tab:!selected {
    margin-top: 2px;
}

/* Disabled tab style */
QTabBar::tab:disabled {
    background: solid #646464;
    border-color: #969696;
    border-bottom-color: #C2C7CB;
    color: #787878;
}

/* Group box style */
QGroupBox {    
    background-color: rgb(70, 70, 70);
    border: 2px solid #808080;
    border-radius: 5px;
    margin-top: 3ex;
}

/* Group box title style */
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;    
    color: #969696;
}

/* Enabled label color */
QLabel::enabled {
    color: rgb(210, 210, 210);
}

/* Disabled label color */
QLabel::disabled {
    color: rgb(120, 120, 120);
}

/* Status bar style */
QLabel#statusBar {
    border: 2px solid #969696;
    border-radius: 4px
}

/* Analog gain label style */
QLabel#gainLabelA {
    margin-bottom: 6px;
    margin-left: -2px
}

/* Digital gain label style */
QLabel#gainLabelD {
    margin-bottom: 6px;
    margin-left: -2px
}

/* Enabled tool button style. For example camera scroll buttons */
QToolButton::enabled {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(50, 50, 50);
    color: rgb(210, 210, 210);   
}

/* Pressed tool button style */
QToolButton:pressed {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(180, 180, 180);
    color: rgb(30, 30, 30);
}

/* Disabled tool button style */
QToolButton::disabled {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(100, 100, 100);
    color: rgb(120, 120, 120);
}

/* Enabled unchecked check box indicator style. For example preview check box */
QCheckBox::indicator:enabled:unchecked {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(70, 70, 70);   
}

/* Enabled checked check box indicator style */
QCheckBox::indicator:enabled:checked {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(180, 0, 0);   
}

/* Enabled check box label color */ 
QCheckBox::enabled {
    color: rgb(210, 210, 210);
}

/* Disabled unchecked check box indicator style */
QCheckBox::indicator:disabled:unchecked {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(100, 100, 100);   
}

/* Disabled checked check box indicator style */
QCheckBox::indicator:disabled:checked {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(100, 0, 0);   
}

/* Disabled check box label color */ 
QCheckBox::disabled {
    color: rgb(120, 120, 120);
}

/* Enabled push button style. For example start push button */
QPushButton::enabled {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(50, 50, 50);
    color: rgb(210, 210, 210);    
}

/* Enabled pressed push button style */
QPushButton::enabled:pressed {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(180, 180, 180);
    color: rgb(30, 30, 30);    
}

/* Disabled push button style */
QPushButton::disabled {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(100, 100, 100);
    color: rgb(120, 120, 120);
}

/* Enabled line edit style. For example configuration file line edit */
QLineEdit::enabled {
    border: 2px solid #969696;
    border-radius: 4px;    
    background-color: rgb(50, 50, 50);
    selection-background-color: rgb(0, 80, 0);
    color: rgb(210, 210, 210);
}

/* Disabled line edit style */
QLineEdit::disabled {
    border: 2px solid #969696;
    border-radius: 4px;    
    background-color: rgb(100, 100, 100);    
    color: rgb(120, 120, 120);
}

/* Enabled spin box an double spin box style. For example last frame spin box */
QSpinBox::enabled, QDoubleSpinBox::enabled {    
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(50, 50, 50);
    selection-background-color: rgb(0, 80, 0);
    color: rgb(210, 210, 210);
}

/* Disabled spin box an double spin box style */
QSpinBox::disabled, QDoubleSpinBox::disabled {    
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(100, 100, 100);
    color: rgb(120, 120, 120);
}

/* Enabled spin box and double spinbox up button style */
QSpinBox::up-button:enabled, QDoubleSpinBox::up-button:enabled {
    subcontrol-origin: content;
    subcontrol-position: top right;
    border-top: none;
    border-bottom:none;       
    border-left: 1px solid #969696;
    border-right: none; 
    border-top-right-radius: 2px;    
    width: 16px;    
    background-color: rgb(60, 60, 60);
}

/* Disabled spin box and double spinbox up button style */
QSpinBox::up-button:disabled, QDoubleSpinBox::up-button:disabled {
    subcontrol-origin: content;
    subcontrol-position: top right;
    border-top: none;
    border-bottom:none;       
    border-left: 1px solid #969696;
    border-right: none; 
    border-top-right-radius: 2px;    
    width: 16px;    
    background-color: rgb(100, 100, 100);
}

/* Pressed spin box and double spinbox up button style */
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {   
    border-bottom: 1px solid #323232;
    border-left: 2px solid #323232;
    background-color: rgb(180, 180, 180);
}

/* Enabled spin box and double spinbox up arrow image */
QSpinBox::up-arrow:enabled, QDoubleSpinBox::up-arrow:enabled {
    image: url(./Resources/arrow-up-en.png);
    width: 7px;
    height: 7px;
}

/* Disabled spin box up arrow image */
QSpinBox::up-arrow:disabled, QSpinBox::up-arrow:off {
   image: url(./Resources/arrow-up-dis.png);
   width: 7px;
   height: 7px;
}

/* Disabled double spin box up arrow image */
QDoubleSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:off {
   image: url(./Resources/arrow-up-dis.png);
   width: 7px;
   height: 7px;
}

/* Enabled spin box and double spinbox down arrow style */
QSpinBox::down-button:enabled, QDoubleSpinBox::down-button:enabled {
    subcontrol-origin: content;
    subcontrol-position: bottom right;
    border-top : none;
    border-bottom: none;    
    border-left: 1px solid #969696;
    border-right: none;
    border-bottom-right-radius: 2px;
    width: 16px;
    background-color: rgb(60, 60, 60);
}

/* Disabled spin box and double spinbox down arrow style */
QSpinBox::down-button:disabled, QDoubleSpinBox::down-button:disabled {
    subcontrol-origin: content;
    subcontrol-position: bottom right;
    border-top : none;
    border-bottom: none;    
    border-left: 1px solid #969696;
    border-right: none;
    border-bottom-right-radius: 2px;
    width: 16px;
    background-color: rgb(100, 100, 100);
}

/* Pressed spin box and double spinbox down button style */
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
    border-top: 2px solid #323232;
    border-left: 1px solid #323232;
    background-color: rgb(180, 180, 180);
}

/* Enabled spin box and double spinbox down arrow image */
QSpinBox::down-arrow:enabled, QDoubleSpinBox::down-arrow:enabled {
    image: url(./Resources/arrow-down-en.png);
    width: 7px;
    height: 7px;
}

/* Disabled spin box down arrow image */
QSpinBox::down-arrow:disabled, QSpinBox::down-arrow:off {
   image: url(./Resources/arrow-down-dis.png);
   width: 7px;
   height: 7px;
}

/* Disabled double spin box down arrow image */
QDoubleSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:off {
   image: url(./Resources/arrow-down-dis.png);
   width: 7px;
   height: 7px;
}

/* Minimum exposure box style */
QDoubleSpinBox#exposureBoxMin {
    border: 1px solid #969696;    
    border-radius: 4px;    
}

/* Nominal exposure box style */
QDoubleSpinBox#exposureBox {
    border: 1px solid #969696;    
    border-radius: 4px;    
}

/* Maximum exposure box style */
QDoubleSpinBox#exposureBoxMax {
    border: 1px solid #969696;    
    border-radius: 4px;    
}

/* FPS box style */
QDoubleSpinBox#FPSdoubleSpinBox {
    border: 1px solid #969696;    
    border-radius: 4px;    
}

/* Analog gain box style */
QDoubleSpinBox#gainBoxA {
    border: 1px solid #969696;    
    border-radius: 4px;
    margin-bottom: 6px;
}

/* Digital gain box style */
QDoubleSpinBox#gainBoxD {
    border: 1px solid #969696;    
    border-radius: 4px;
    margin-bottom: 6px;
}

/* Combo box style. For example white balance comb box */
QComboBox {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(50, 50, 50);
    selection-background-color: rgb(0, 80, 0);
    color: rgb(210, 210, 210);
}

/* Disabled combo box style */
QComboBox:disabled {
    border: 2px solid #969696;
    border-radius: 4px;
    background-color: rgb(100, 100, 100);    
    color: rgb(120, 120, 120);
}

/* Combo box list colors */
QListView {
    background-color: rgb(50, 50, 50);
    selection-background-color: rgb(0, 80, 0);
    color: rgb(210, 210, 210);
}

/* Combo box button style */
QComboBox::drop-down {
    subcontrol-origin: content;
    subcontrol-position: top right;
    width: 16px;
    border-top : none;
    border-bottom: none;    
    border-left: 1px solid #969696;
    border-right: none;    
    border-top-right-radius: 2px;
    border-bottom-right-radius: 2px;
    background-color: rgb(60, 60, 60);
}

/* Combo box disabled button style */
QComboBox::drop-down:disabled {
    subcontrol-origin: content;
    subcontrol-position: top right;
    width: 16px;
    border-top : none;
    border-bottom: none;    
    border-left: 1px solid #969696;
    border-right: none;    
    border-top-right-radius: 2px;
    border-bottom-right-radius: 2px;
    background-color: rgb(100, 100, 100);
}

/* Combo box arrow image */
QComboBox::down-arrow {
    image: url(./Resources/arrow-down-en.png);
    width: 7px;
    height: 7px;
}

/* Combo box disabled arrow image */
QComboBox::down-arrow:disabled {
    image: url(./Resources/arrow-down-dis.png);
    width: 7px;
    height: 7px;
}

/* Combo box arrow movement */ 
QComboBox::down-arrow:on {
    top: 1px;
    left: 1px;
}

/* Slider groove style. For example saturation slider */
QSlider::groove:horizontal {
    border: 1px solid #969696;
    border-radius: 2px;
    height: 4px;
    background: solid #464646;   
}

/* Enabled right side of slider style */
QSlider::add-page:horizontal:enabled {
    border: 1px solid #969696;
    border-radius: 2px;
    background: solid #464646;    
}

/* Disabled right side of slider style */
QSlider::add-page:horizontal:disabled {
    border: 1px solid #969696;
    border-radius: 2px;    
    background: solid #646464;    
}

/* Enabled left side of slider style */
QSlider::sub-page:horizontal:enabled {
    border: 1px solid #969696;
    border-radius: 2px;    
    background: solid #005000;    
}

/* Disabled left side of slider style */
QSlider::sub-page:horizontal:disabled {
    border: 1px solid #969696;
    border-radius: 2px;
    background: solid #002800;    
}

/* Slider handle style */
QSlider::handle:horizontal {
    border: 1px solid #969696;
    border-radius: 2px;
    background: solid #323232;    
    height: 8px;
    width: 10px;
    margin: -4px 0;
}

/* Disabled slider handle style */
QSlider::handle:horizontal:disabled {    
    background: solid #646464;    
}

/* Help on pop-ups style */
QToolTip {
    border: 1px solid #969696;    
    background: solid #464646;
    color: #d2d2d2;
}

/* QFileDialog colors */
QTreeView {
    background-color: rgb(50, 50, 50);
    selection-background-color: rgb(0, 80, 0);
    color: rgb(210, 210, 210);
}
QHeaderView {
    background-color: rgb(80, 80, 80);    
    color: rgb(210, 210, 210);    
}

QHeaderView::up-arrow {
    image: url(./Resources/header-arrow-up.png);
}

QHeaderView::down-arrow {
    image: url(./Resources/header-arrow-down.png);
}

QScrollBar:horizontal
    {
        height: 18px;
        margin: 3px 16px 3px 16px;
        border: 1px transparent #2A2929;
        border-radius: 2px;
        background-color: rgb(0, 80, 0);
    }

QScrollBar::handle:horizontal
{
    background-color: rgb(80, 80, 80);
    min-width: 5px;
    border-radius: 2px;
}

QScrollBar::add-line:horizontal
{
    margin: 0px 3px 0px 3px;
    border-image: url(./Resources/scroll-arrow-right.png);
    width: 16px;
    height: 16px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:horizontal
{
    margin: 0px 3px 0px 3px;
    border-image: url(./Resources/scroll-arrow-left.png);
    height: 16px;
    width: 16px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}

QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal
{
    background: none;
}


QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
{
    background: none;
}

QScrollBar:vertical
{
    background-color: rgb(0, 80, 0);
    width: 18px;
    margin: 16px 3px 16px 3px;
    border: 1px transparent #2A2929;
    border-radius: 2px;
}

QScrollBar::handle:vertical
{
    background-color: rgb(80, 80, 80);
    min-height: 5px;
    border-radius: 4px;
}

QScrollBar::add-line:vertical
{
    margin: 3px 0px 3px 0px;
    border-image: url(./Resources/header-arrow-down.png);
    height: 16px;
    width: 16px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical
{
    margin: 3px 0px 3px 0px;
    border-image: url(./Resources/header-arrow-up.png);
    height: 16px;
    width: 16px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical
{
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
{
    background: none;
}
'''

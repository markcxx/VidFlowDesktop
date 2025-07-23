# coding:utf-8
from typing import Union, Tuple, Dict, Set
from PyQt5.QtCore import pyqtProperty, QRectF
from PyQt5.QtGui import QIcon, QPainter, QColor, QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtXml import QDomDocument
from PyQt5.QtCore import QFile, Qt
from qfluentwidgets import IconWidget, FluentIconBase
import os


class SvgColorProcessor:
    """SVG颜色处理器，负责修改SVG文件的颜色属性"""
    
    # SVG元素标签配置
    SVG_TAGS = {
        'path', 'circle', 'rect', 'ellipse', 'polygon', 
        'polyline', 'line', 'g', 'svg'
    }
    
    # 需要默认填充颜色的形状元素
    SHAPE_TAGS = {'circle', 'rect', 'ellipse', 'polygon'}
    
    # 忽略的颜色值
    IGNORED_VALUES = {'none', 'transparent', ''}
    
    @classmethod
    def modifySvgColor(cls, svgPath: str, color: QColor) -> str:
        """修改SVG文件的颜色属性
        
        Parameters
        ----------
        svgPath : str
            SVG文件路径
        color : QColor
            目标颜色
            
        Returns
        -------
        str
            修改后的SVG代码
        """
        if not cls._isValidSvgPath(svgPath):
            return ""
        
        dom = cls._loadSvgDom(svgPath)
        if dom is None:
            return ""
        
        cls._processAllElements(dom, color)
        return dom.toString()
    
    @classmethod
    def _isValidSvgPath(cls, svgPath: str) -> bool:
        """检查SVG路径是否有效"""
        if not svgPath.lower().endswith('.svg'):
            return False
        
        # 支持Qt资源路径
        if svgPath.startswith(':/'):
            file = QFile(svgPath)
            return file.exists()
        
        # 支持文件系统路径
        return os.path.exists(svgPath)
    
    @classmethod
    def _loadSvgDom(cls, svgPath: str) -> QDomDocument:
        """加载SVG文件为DOM文档"""
        file = QFile(svgPath)
        if not file.open(QFile.ReadOnly):
            return None
        
        dom = QDomDocument()
        success = dom.setContent(file.readAll())
        file.close()
        
        return dom if success else None
    
    @classmethod
    def _processAllElements(cls, dom: QDomDocument, color: QColor):
        """处理所有SVG元素的颜色属性"""
        colorName = color.name()
        
        for tagName in cls.SVG_TAGS:
            nodes = dom.elementsByTagName(tagName)
            for i in range(nodes.length()):
                element = nodes.at(i).toElement()
                cls._processElement(element, tagName, colorName)
    
    @classmethod
    def _processElement(cls, element, tagName: str, colorName: str):
        """处理单个SVG元素的颜色属性"""
        # 处理描边颜色
        cls._processStrokeAttribute(element, colorName)
        
        # 处理填充颜色
        cls._processFillAttribute(element, tagName, colorName)
    
    @classmethod
    def _processStrokeAttribute(cls, element, colorName: str):
        """处理stroke属性"""
        if element.hasAttribute('stroke'):
            strokeValue = element.attribute('stroke')
            if cls._shouldUpdateColor(strokeValue):
                element.setAttribute('stroke', colorName)
    
    @classmethod
    def _processFillAttribute(cls, element, tagName: str, colorName: str):
        """处理fill属性"""
        if element.hasAttribute('fill'):
            fillValue = element.attribute('fill')
            if cls._shouldUpdateColor(fillValue):
                element.setAttribute('fill', colorName)
        elif tagName in cls.SHAPE_TAGS:
            # 对于形状元素，如果没有fill属性，默认添加
            element.setAttribute('fill', colorName)
    
    @classmethod
    def _shouldUpdateColor(cls, value: str) -> bool:
        """判断是否应该更新颜色值"""
        return (value == 'currentColor' or 
                value not in cls.IGNORED_VALUES)


class ColorIconWidget(IconWidget):
    """支持动态颜色修改的图标组件
    
    继承自qfluentwidgets的IconWidget，提供setColor和getColor方法
    支持SVG图标的动态颜色修改
    """
    
    def __init__(self, svgPath: Union[str, FluentIconBase] = None, parent: QWidget = None):
        """初始化ColorIconWidget
        
        Parameters
        ----------
        svgPath : str or FluentIconBase, optional
            SVG文件路径或FluentIconBase枚举值
        parent : QWidget, optional
            父组件
        """
        super().__init__(parent)
        
        # 处理不同类型的输入参数
        if isinstance(svgPath, FluentIconBase):
            self._svgPath = svgPath.path()
        else:
            self._svgPath = svgPath or ""
            
        self._currentColor = QColor(0, 0, 0)  # 默认黑色
        self._iconCache = {}  # 图标缓存
        
        if self._svgPath:
            self._updateIcon()
    
    def setSvgPath(self, svgPath: Union[str, FluentIconBase]):
        """设置SVG文件路径
        
        Parameters
        ----------
        svgPath : str or FluentIconBase
            SVG文件路径或FluentIconBase枚举值
        """
        # 处理不同类型的输入参数
        if isinstance(svgPath, FluentIconBase):
            new_path = svgPath.path()
        else:
            new_path = svgPath or ""
            
        if self._svgPath != new_path:
            self._svgPath = new_path
            self._iconCache.clear()  # 清除缓存
            self._updateIcon()
    
    def getSvgPath(self) -> str:
        """获取SVG文件路径
        
        Returns
        -------
        str
            SVG文件路径
        """
        return self._svgPath
    
    def setColor(self, color: Union[QColor, str, Tuple[int, int, int]]):
        """设置图标颜色
        
        Parameters
        ----------
        color : QColor | str | Tuple[int, int, int]
            图标颜色，支持QColor对象、颜色字符串或RGB元组
        """
        newColor = self._normalizeColor(color)
        if newColor != self._currentColor:
            self._currentColor = newColor
            self._updateIcon()
    
    def getColor(self) -> QColor:
        """获取当前图标颜色
        
        Returns
        -------
        QColor
            当前图标颜色
        """
        return QColor(self._currentColor)
    
    def createIconWithColor(self, color: QColor, size: Tuple[int, int] = (24, 24)) -> QIcon:
        """创建指定颜色的图标
        
        Parameters
        ----------
        color : QColor
            图标颜色
        size : Tuple[int, int], optional
            图标尺寸，默认(24, 24)
            
        Returns
        -------
        QIcon
            指定颜色的图标
        """
        if not self._svgPath:
            return QIcon()
        
        # 检查缓存
        cacheKey = (color.name(), size)
        if cacheKey in self._iconCache:
            return self._iconCache[cacheKey]
        
        # 创建新图标
        icon = self._createIcon(color, size)
        self._iconCache[cacheKey] = icon
        return icon
    
    def renderWithColor(self, painter: QPainter, rect: QRectF, color: QColor):
        """直接绘制指定颜色的图标
        
        Parameters
        ----------
        painter : QPainter
            绘制器
        rect : QRectF
            绘制区域
        color : QColor
            图标颜色
        """
        if not self._svgPath:
            return
        
        modifiedSvg = SvgColorProcessor.modifySvgColor(self._svgPath, color)
        if modifiedSvg:
            renderer = QSvgRenderer(modifiedSvg.encode())
            renderer.render(painter, rect)
    
    def _normalizeColor(self, color: Union[QColor, str, Tuple[int, int, int]]) -> QColor:
        """标准化颜色输入
        
        Parameters
        ----------
        color : QColor | str | Tuple[int, int, int]
            输入颜色
            
        Returns
        -------
        QColor
            标准化的QColor对象
        """
        if isinstance(color, QColor):
            return color
        elif isinstance(color, str):
            return QColor(color)
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            return QColor(color[0], color[1], color[2])
        else:
            return QColor(0, 0, 0)  # 默认黑色
    
    def _updateIcon(self):
        """更新图标显示"""
        if self._svgPath:
            icon = self.createIconWithColor(self._currentColor)
            self.setIcon(icon)
    
    def _createIcon(self, color: QColor, size: Tuple[int, int]) -> QIcon:
        """创建图标
        
        Parameters
        ----------
        color : QColor
            图标颜色
        size : Tuple[int, int]
            图标尺寸
            
        Returns
        -------
        QIcon
            创建的图标
        """
        modifiedSvg = SvgColorProcessor.modifySvgColor(self._svgPath, color)
        if not modifiedSvg:
            return QIcon()
        
        # 创建QPixmap并绘制SVG
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        renderer = QSvgRenderer(modifiedSvg.encode())
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    
    # Qt属性
    color = pyqtProperty(QColor, getColor, setColor)
    svgPath = pyqtProperty(str, getSvgPath, setSvgPath)
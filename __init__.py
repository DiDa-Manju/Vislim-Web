import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, List, Any, Dict

class BackgroundConflictError(Exception):
    """当同时设置了多种背景时抛出的异常"""
    pass


class App:
    """Vislim Web 应用主类，支持纯色、图片和渐变色背景"""

    def __init__(
            self,
            title: Optional[str] = None,
            icon: Optional[str] = None,
            bg_color: Optional[str] = None,  # 颜色背景，如 "blue", "#f0f0f0"
            bg_image: Optional[str] = None,  # 图片背景，如 "/static/bg.jpg"
            bg_gradient: Optional[dict] = None  # 渐变色背景，格式见下文
    ) -> None:
        """
        初始化 App 实例
        :param title: 浏览器标签页标题，默认为 "Vislim Web"
        :param icon: 图标文件路径（如 favicon.ico），若提供则必须存在
        :param bg_color: 纯色背景，与 bg_image、bg_gradient 互斥
        :param bg_image: 图片背景，与 bg_color、bg_gradient 互斥
        :param bg_gradient: 渐变色背景，格式为字典，例如：
            {
                "type": "linear",                 # 目前仅支持线性渐变
                "angle": 45,                       # 可选，渐变方向角度（0~360），默认0（从上到下）
                "colors": ["red", "blue"],          # 必须，颜色列表
                "stops": [0, 100]                   # 可选，颜色停靠点（百分比或像素值如 "10px"），长度应与 colors 相同
            }
        """
        self.title = title or "Vislim Web"
        self.icon = icon
        if icon and not os.path.isfile(icon):
            raise FileNotFoundError(f"Icon file not found: {icon}")

        # 背景设置互斥检查
        bg_provided = sum([bg_color is not None, bg_image is not None, bg_gradient is not None])
        if bg_provided > 1:
            raise BackgroundConflictError("只能设置一种背景：纯色、图片或渐变色")
        self.bg_color = bg_color
        self.bg_image = bg_image
        self.bg_gradient = bg_gradient

        self.children: List[Any] = []

    def add(self, component: Any) -> None:
        """添加组件到 App"""
        self.children.append(component)

    def start(self, host: str = '127.0.0.1', port: int = 8080, open_browser: bool = True) -> None:
        server = HTTPServer((host, port), self._create_handler())
        print(f"Vislim Web app running at http://{host}:{port}/")
        if open_browser:
            webbrowser.open(f"http://{host}:{port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

    def _create_handler(self):
        app_instance = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html = self._render_index()
                    self.wfile.write(html.encode('utf-8'))
                elif self.path == '/favicon.ico' and app_instance.icon:
                    self._serve_icon()
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'404 Not Found')

            def _render_index(self) -> str:
                title = app_instance.title
                icon_link = f'<link rel="icon" href="/favicon.ico">' if app_instance.icon else ''

                # 生成背景样式
                body_style = ""
                if app_instance.bg_color:
                    body_style = f"background-color: {app_instance.bg_color};"
                elif app_instance.bg_image:
                    body_style = f"background-image: url('{app_instance.bg_image}'); background-size: cover; background-position: center; background-repeat: no-repeat;"
                elif app_instance.bg_gradient:
                    # 解析渐变色字典
                    grad = app_instance.bg_gradient
                    grad_type = grad.get("type", "linear")
                    if grad_type != "linear":
                        # 目前仅支持线性渐变，可扩展
                        raise ValueError(f"不支持的渐变类型: {grad_type}")

                    # 处理角度（默认0度 = 从上到下）
                    angle = grad.get("angle", 0)
                    # 处理颜色和停靠点
                    colors = grad.get("colors", [])
                    if not colors:
                        raise ValueError("渐变色必须提供 colors 列表")

                    stops = grad.get("stops")
                    if stops:
                        if len(stops) != len(colors):
                            raise ValueError("stops 列表长度必须与 colors 相同")
                        # 将数值转换为带单位的字符串（默认 %）
                        stop_strs = []
                        for s in stops:
                            if isinstance(s, (int, float)):
                                stop_strs.append(f"{s}%")
                            else:
                                stop_strs.append(str(s))
                        color_stops = [f"{c} {s}" for c, s in zip(colors, stop_strs)]
                    else:
                        # 默认均匀分布
                        color_stops = colors

                    # 构建 CSS 渐变字符串
                    gradient_css = f"linear-gradient({angle}deg, {', '.join(color_stops)})"
                    body_style = f"background-image: {gradient_css}; background-size: cover;"

                # 收集所有子组件的 HTML
                body_content = ''.join(child.render() for child in app_instance.children)

                return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {icon_link}
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            min-height: 100%;
        }}
        body {{
            font-family: sans-serif;
            {body_style}
        }}
    </style>
</head>
<body>
    {body_content}
</body>
</html>
'''

            def _serve_icon(self) -> None:
                try:
                    with open(app_instance.icon, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    ext = os.path.splitext(app_instance.icon)[1].lower()
                    if ext == '.ico':
                        content_type = 'image/x-icon'
                    elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.svg'):
                        content_type = f'image/{ext[1:]}'
                    else:
                        content_type = 'application/octet-stream'
                    self.send_header('Content-Type', content_type)
                    self.end_headers()
                    self.wfile.write(content)
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Error serving icon: {e}".encode())

        return Handler

class Text:
    """文本组件（使用 p 标签），支持多种样式"""

    def __init__(
        self,
        app: App,
        text: str = "",
        color: str = "black",
        bg: Optional[str] = None,
        font_size: Optional[int] = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        border: Optional[str] = None,
        border_radius: Optional[str] = None,
        padding: Optional[str] = None,
        margin: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        align: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        self.app = app
        self.text = text
        self.color = color
        self.bg = bg
        self.font_size = font_size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.border = border
        self.border_radius = border_radius
        self.padding = padding
        self.margin = margin
        self.width = width
        self.height = height
        self.align = align
        self.extra_styles = kwargs

    def show(self) -> 'Text':
        self.app.add(self)
        return self

    def render(self) -> str:
        styles: List[str] = []
        styles.append(f"color: {self.color};")
        if self.bg:
            styles.append(f"background-color: {self.bg};")
        if self.font_size:
            styles.append(f"font-size: {self.font_size}px;")
        if self.bold:
            styles.append("font-weight: bold;")
        if self.italic:
            styles.append("font-style: italic;")
        if self.underline:
            styles.append("text-decoration: underline;")
        if self.border:
            styles.append(f"border: {self.border};")
        if self.border_radius:
            styles.append(f"border-radius: {self.border_radius};")
        if self.padding:
            styles.append(f"padding: {self.padding};")
        if self.margin:
            styles.append(f"margin: {self.margin};")
        if self.width:
            styles.append(f"width: {self.width};")
        if self.height:
            styles.append(f"height: {self.height};")
        if self.align:
            styles.append(f"text-align: {self.align};")
        for key, value in self.extra_styles.items():
            css_key = key.replace('_', '-')
            styles.append(f"{css_key}: {value};")
        style_str = ' '.join(styles)
        return f'<p style="{style_str}">{self.text}</p>'


class H:
    """标题组件，对应 h1 ~ h6，支持多种样式"""

    def __init__(
        self,
        app: App,
        level: int,
        text: str = "",
        color: str = "black",
        bg: Optional[str] = None,
        font_size: Optional[int] = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        border: Optional[str] = None,
        border_radius: Optional[str] = None,
        padding: Optional[str] = None,
        margin: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        align: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        if level not in range(1, 7):
            raise ValueError("level must be an integer between 1 and 6")
        self.app = app
        self.level = level
        self.text = text
        self.color = color
        self.bg = bg
        self.font_size = font_size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.border = border
        self.border_radius = border_radius
        self.padding = padding
        self.margin = margin
        self.width = width
        self.height = height
        self.align = align
        self.extra_styles = kwargs

    def show(self) -> 'H':
        self.app.add(self)
        return self

    def render(self) -> str:
        styles: List[str] = []
        styles.append(f"color: {self.color};")
        if self.bg:
            styles.append(f"background-color: {self.bg};")
        if self.font_size:
            styles.append(f"font-size: {self.font_size}px;")
        if self.bold:
            styles.append("font-weight: bold;")
        if self.italic:
            styles.append("font-style: italic;")
        if self.underline:
            styles.append("text-decoration: underline;")
        if self.border:
            styles.append(f"border: {self.border};")
        if self.border_radius:
            styles.append(f"border-radius: {self.border_radius};")
        if self.padding:
            styles.append(f"padding: {self.padding};")
        if self.margin:
            styles.append(f"margin: {self.margin};")
        if self.width:
            styles.append(f"width: {self.width};")
        if self.height:
            styles.append(f"height: {self.height};")
        if self.align:
            styles.append(f"text-align: {self.align};")
        for key, value in self.extra_styles.items():
            css_key = key.replace('_', '-')
            styles.append(f"{css_key}: {value};")
        style_str = ' '.join(styles)
        tag = f"h{self.level}"
        return f'<{tag} style="{style_str}">{self.text}</{tag}>'


class Button:
    """按钮组件，支持悬停效果（颜色、背景、边框变化），所有样式均通过<style>定义"""

    def __init__(
        self,
        app: App,
        text: str = "",
        text_color: str = "black",
        button_color : Optional[str] = None,
        font_size: Optional[int] = None,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        border: Optional[str] = None,
        border_radius: Optional[str] = None,
        padding: Optional[str] = None,
        margin: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        align: Optional[str] = None,
        # 悬停属性
        hover_color: Optional[str] = None,
        hover_bg: Optional[str] = None,
        hover_border: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        self.app = app
        self.text = text
        self.text_color = text_color
        self.button_color = button_color
        self.font_size = font_size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.border = border
        self.border_radius = border_radius
        self.padding = padding
        self.margin = margin
        self.width = width
        self.height = height
        self.align = align
        self.hover_color = hover_color
        self.hover_bg = hover_bg
        self.hover_border = hover_border
        self.extra_styles = kwargs

    def show(self) -> 'Button':
        self.app.add(self)
        return self

    def render(self) -> str:
        # 生成唯一ID（以字母开头，符合HTML规范）
        elem_id = f"btn{id(self)}"

        # 构建基础样式字典
        base_styles = {
            "color": self.text_color,
            "background-color": self.button_color,
            "font-size": f"{self.font_size}px" if self.font_size else None,
            "font-weight": "bold" if self.bold else None,
            "font-style": "italic" if self.italic else None,
            "text-decoration": "underline" if self.underline else None,
            "border": self.border,
            "border-radius": self.border_radius,
            "padding": self.padding,
            "margin": self.margin,
            "width": self.width,
            "height": self.height,
            "text-align": self.align,
        }
        # 合并额外样式
        for key, value in self.extra_styles.items():
            base_styles[key.replace('_', '-')] = value

        # 过滤掉值为None的项，并生成CSS规则字符串
        base_css = '; '.join(f"{k}: {v}" for k, v in base_styles.items() if v is not None)

        # 构建悬停样式字典
        hover_styles = {}
        if self.hover_color:
            hover_styles["color"] = self.hover_color
        if self.hover_bg:
            hover_styles["background-color"] = self.hover_bg
        if self.hover_border:
            hover_styles["border"] = self.hover_border
        hover_css = '; '.join(f"{k}: {v}" for k, v in hover_styles.items()) if hover_styles else None

        # 生成<style>块
        style_parts = [f"#{elem_id} {{ {base_css} }}"]
        if hover_css:
            style_parts.append(f"#{elem_id}:hover {{ {hover_css} }}")
        style_tag = f"<style>{' '.join(style_parts)}</style>"

        # 按钮HTML（不带内联样式）
        button_html = f'<button id="{elem_id}">{self.text}</button>'
        return style_tag + button_html
class IconCard:
    def __init__(self, app, icon="★", text="",
                 icon_color="white", icon_bg="black", icon_size=24,
                 text_color="black", text_size=14, text_bold=False,
                 border_color="white", border_width="2px",
                 hover_icon_color="black", hover_icon_bg="white",
                 hover_text_color="white", hover_border_color="black",
                 align="center", padding="10px", margin=None, width=None,
                 **kwargs):
        self.app = app
        self.icon = icon
        self.text = text
        self.icon_color = icon_color
        self.icon_bg = icon_bg
        self.icon_size = icon_size
        self.text_color = text_color
        self.text_size = text_size
        self.text_bold = text_bold
        self.border_color = border_color
        self.border_width = border_width
        self.hover_icon_color = hover_icon_color
        self.hover_icon_bg = hover_icon_bg
        self.hover_text_color = hover_text_color
        self.hover_border_color = hover_border_color
        self.align = align
        self.padding = padding
        self.margin = margin
        self.width = width
        self.extra_styles = kwargs

    def show(self):
        self.app.add(self)
        return self

    def render(self):
        # 生成唯一ID（用于CSS选择器）
        elem_id = f"ic{id(self)}"

        # 构建基础CSS（使用类名+ID组合，避免内联样式）
        css = f"""
            <style>
                #{elem_id} {{
                    display: inline-flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    padding: {self.padding};
                    margin: {self.margin or '0'};
                    width: {self.width or 'auto'};
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                    {self._dict_to_css(self.extra_styles)}
                }}
                #{elem_id} .icon-circle {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background-color: {self.icon_bg};
                    color: {self.icon_color};
                    font-size: {self.icon_size}px;
                    border: {self.border_width} solid {self.border_color};
                    transition: all 0.3s ease;
                }}
                #{elem_id} .icon-text {{
                    color: {self.text_color};
                    font-size: {self.text_size}px;
                    font-weight: {'bold' if self.text_bold else 'normal'};
                    margin-top: 5px;
                    transition: color 0.3s ease;
                }}
                /* 悬停样式 */
                #{elem_id}:hover .icon-circle {{
                    background-color: {self.hover_icon_bg};
                    color: {self.hover_icon_color};
                    border-color: {self.hover_border_color};
                }}
                #{elem_id}:hover .icon-text {{
                    color: {self.hover_text_color};
                }}
                /* 即使未设置悬停参数，也添加一个默认背景变化让用户感知可点击 */
                #{elem_id}:hover {{
                    background-color: rgba(0,0,0,0.03);
                }}
            </style>
        """

        # 构建HTML结构（不再包含内联样式）
        html = f"""
            {css}
            <div id="{elem_id}">
                <div class="icon-circle">{self.icon}</div>
                <div class="icon-text">{self.text}</div>
            </div>
        """
        return html

    def _dict_to_css(self, d):
        """辅助方法：将字典转换为CSS属性字符串"""
        return '; '.join(f"{k.replace('_', '-')}: {v}" for k, v in d.items())


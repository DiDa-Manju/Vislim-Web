# Vislim-Web
Vislim is a Python web framework that lets you build web pages using only Python, without writing HTML, CSS or JavaScript. It uses server-side rendering and provides built-in components.  Vislim 是一个 Python Web 框架，让你只用 Python 构建网页，无需编写 HTML、CSS 或 JavaScript。它采用服务端渲染，并提供内置组件。
Quick Start | 快速开始
python
from vislim import App, Text, Button

app = App(title="My App")
Text(app, text="Hello Vislim!", font_size=24).show()
Button(app, text="Click Me").show()
app.start()
Then open http://127.0.0.1:8080 | 然后打开 http://127.0.0.1:8080

Components | 组件
Text

Text(app, text="Hello", color="blue", font_size=20, bold=True)

Button

Button(app, text="Submit", button_color="green", hover_bg="darkgreen")

IconCard

IconCard(app, icon="★", text="Star", hover_icon_bg="gold")

Background Gradient | 背景渐变

app = App(bg_gradient={"colors": ["red", "blue"], "angle": 45})

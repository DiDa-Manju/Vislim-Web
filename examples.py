from vislim import App, Text, Button
if __name__ == "examples":
  app = App(title="Hello Vislim")
  Text(app, text="Welcome to Vislim!", font_size=24, color="blue").show()
  Button(app, text="Click Me", button_color="lightgray", hover_bg="gray").show()
  app.start()

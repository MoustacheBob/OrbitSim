from ursina import *

app = Ursina()

cube = Entity(model = 'cube', color = rgb(200,0,0), collider='box')

def cubeclick():
    cube.rotate((45,45,45))

cube.on_click = cubeclick

window.color = (0.1)

EditorCamera()

app.run()
from ursina import *


#Definitions:   Distances (radius, apoapsis, periapsis) in 1000km
#               Mass in metric Tons           

app = Ursina()

class GravBody(Sprite):
    def __init__(self,radius = 1, mass = 6.583 * 10**21, apoapsis = 0, periapsis = None, draw_soi = False, texture=None, ppu = None, **kwargs):
        super().__init__(texture, ppu, **kwargs)
        if periapsis == None: periapsis = apoapsis
        self.double_sided_setter(True)
        self.scale = radius * 2 / self.model_bounds.size.x

        # #Soi construction
        # if draw_soi == True:
        #     self.Soi = Sprite(texture='Soi2', parent=self)
        #     Soi_radius = 

    def update(self):
        self.look_at(camera.world_position)


Earth = GravBody(radius=6.3781, texture='Earth')

# earth = Sprite(texture='Earth', double_sided = True)
# earth_target_radius = 6.3781
# earth_scale = earth_target_radius*2 / earth.model_bounds.size.x
# earth.scale = earth_scale

Moon = GravBody(radius=1.737, texture='FullMoon', position = (384.399,0,0))

#Orbit = Entity(model=Circle(resolution=64, radius=10, mode='line'), color=color.red, scale=3, position=Vec3(20,0,0))

Soi = Sprite(texture='Soi2', scale=20)


#-------Sky----------

sky_tex = load_texture('starBG')

star_sky = Sky(texture=sky_tex)

star_sky.texture_scale = Vec2(5,2)


editor_cam = EditorCamera()
editor_cam.world_position = Vec3(0,0,-100)

def update():
    #earth.look_at(camera.world_position)
    #moon.look_at(camera.world_position)
    pass


app.run()
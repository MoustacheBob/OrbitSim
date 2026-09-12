from ursina import *

app = Ursina()




earth = Sprite(texture='Earth', ppu=1, double_sided = True)
earth_target_radius = 6.3781
earth_scale = earth_target_radius*2 / earth.model_bounds.size.x
earth.scale = earth_scale

moon = Sprite(texture='FullMoon', ppu=1, double_sided = True, position = (384.399,0,0), scale = 1.737)
moon_target_radius = 6.3781
moon_scale = moon_target_radius*2 / moon.model_bounds.size.x
moon.scale = moon_scale


#-------Sky----------

sky_tex = load_texture('starBG')

star_sky = Sky(texture=sky_tex)

star_sky.texture_scale = Vec2(5,2)


editor_cam = EditorCamera()


def update():
    earth.look_at(camera.world_position)
    moon.look_at(camera.world_position)



app.run()
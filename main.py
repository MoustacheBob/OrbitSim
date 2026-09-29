from ursina import *
from config import *
from physics import *
from pathlib import Path
from ursina import application

application.asset_folder = Path(__file__).resolve().parent

#Definitions:   Distances (radius, apoapsis, periapsis) in 1000km
#               Mass in metric Tons           

Text.default_font = 'textures/fonts/pixel_font.ttf'

app = Ursina()

class Visobject(Sprite):
    def __init__(self, radius: float = 1, texture :str = None, orbit_color: str = 'white', customparent: Entity = None, **kwargs):
        super().__init__(texture, **kwargs)
        self.double_sided_setter(True)
        self.world_scale = radius * 2 / 1_000_000 / self.model_bounds.size.x  
        self.position = physobjects[self.name].getState(0)[:3] / 1000000
        self.texture_scale = Vec2(-1, 1)

        
        # if orbit_color is not None:
        #     self.orbit = Entity(model=Circle(segments=100, mode='line'), color=color.__getattribute__(orbit_color), parent=self.parent)
        #     self.orbit.scale = (apoapsis + periapsis) / 2 / self.model_bounds.size.x
        #     self.orbit.rotation_x = 90
        #     self.orbit.position = (apoapsis - periapsis) / 2 / self.model_bounds.size.x, 0, 0
        
        self.phys_object: PhysObject | FixObject = physobjects[self.name]

        #---------soi construction-----
        self.Soi = None
        if self.phys_object.parent is not None:
            self.Soi = Sprite(texture='Soi2', parent=self)
            self.Soi.scale = self.phys_object.soi_radius / radius

        #---------infot text construction-----
        self.info_text = Text(text=f'{self.name}\n{self.phys_object.mass:.2e} kg\n{self.position} m', parent=self, position = (0, -self.model_bounds.size.y/2 -3/self.world_scale.y, 0), origin=(0, 0), enabled=True)
        self.info_text.world_scale = Vec3(-50, 50, 50)
        self.selected_sprite = Sprite(texture='selected', parent = self, world_scale= 7)
        

    def update(self):
        self.world_quaternion = Quat(0,0, 1, 0) * camera.world_quaternion 


def vis_object_maker():
        visobjects = {}

        for object in OBJECTS:

            parent = None
            if object.parent is not None:           #-----> needed to ensure objects receive their actual parent object,
                parent = visobjects[object.parent] #-----> Config needs parents to be before actual object (no sun -> Moon -> Earth)

            visobjects[object.name] = Visobject(
                name=object.name,
                radius=object.radius,
                orbit_color=object.orbit_color if hasattr(object, 'orbit_color') else None,
                texture=object.texture,
                customparent=parent
            )

        return visobjects

visobjects = vis_object_maker()


#-------Sky----------

sky_tex = load_texture('starBG')

star_sky = Sky(texture=sky_tex)

star_sky.texture_scale = Vec2(5,2)


editor_cam = EditorCamera()
editor_cam.world_position = Vec3(0,0,-100)

def update():
    now = timefunc()
    for object in visobjects:
         state = visobjects[object].phys_object.getState(now)[:3]
         visobjects[object].position = Vec3(state[0] / 1000000, state[2] /1000000, state[1]/1000000)
        #  visobjects[object].position.y = state[2] / 1000000
        #  visobjects[object].position.z = state[1] / 1000000

    schedule.run(blocking=False)

app.run()
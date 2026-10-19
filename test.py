from ursina import * 

from ursina import Ursina, ButtonGroup
app = Ursina()
wp = WindowPanel(
    title='Custom Window',
    content=(
        Text('Name:'),
        InputField(name='name_field'),
        Button(text='Submit', color=color.azure),
        Slider(),
        Slider(),
        ButtonGroup(('test', 'eslk', 'skffk'))
        ),
    popup=True
    )
wp.y = wp.panel.scale_y / 2 * wp.scale_y    # center the window panel
wp.layout()

def input(key):
    if key == 'space':
        wp.enabled = True

app.run()
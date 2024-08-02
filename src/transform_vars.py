import vedo

class mode:
    """
    container class for modes for easy acces in the callbacks etc
    """

    def __init__(self, name, key, text, color):
        self.name = name  # mode name e.g. "nasion_pt"
        self.key = key  # key combination for callback check e.g. 'Ctrl+n'
        self.text = text  # text for mode indicator on screen
        self.color = color  # point color as vedo col string eg. Yellow5"

modes = {
    "nasal_tip": mode("nasal_tip", "Ctrl+n", "Nasal Tip Underside Mode", "Green5"),
    "lpa_pt": mode("lpa_pt", "Ctrl+l", "Left Preauricular Point Mode", "Red5"),
    "rpa_pt": mode("rpa_pt", "Ctrl+r", "Right Preauricular Point Mode", "Blue5"),
}

usage_txt = (
    "Right click        :Place point in current mode\n"
    "Left click & drag  :Rotate\n"
    "Wheel click & drag :Move\n"
    "Right click & drag :Zoom (also: SCROLL)\n"
    "CTRL + N           :Nasal Tip Underside mode\n"
    "CTRL + L           :Left Preauricular mode\n"
    "CTRL + R           :Right Preauricular mode\n"
    "q                  :Quit point selection and continue\n"
    "BACKSPACE          :Clear all points\n"
    "h                  :display help in console"
)

usage = vedo.Text2D(
    usage_txt,
    font="Calco",
    pos="top-left",
    s=0.6,
    bg="yellow",
    alpha=0.25,
)

plotter: vedo.Plotter

info_txt: vedo.CornerAnnotation

select_mode: str

mri_mesh: vedo.Mesh
head_mesh: vedo.Mesh

# Points to be collected
mri_fiducial = {"nasal_tip": None, "lpa_pt": None, "rpa_pt": None}
head_fiducial = {"nasal_tip": None, "lpa_pt": None, "rpa_pt": None}

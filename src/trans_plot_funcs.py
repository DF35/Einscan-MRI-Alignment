import vedo
import numpy as np
import transform_vars

# Sets up plotter for fiducial input
def instantiate_plotter():
    plotter = vedo.Plotter(shape=[1,2], axes=False, bg="blackboard", sharecam=False)

    plotter.at(0).add(transform_vars.mri_mesh)
    plotter.at(0).reset_camera()
    plotter.at(1).add(transform_vars.head_mesh)
    plotter.at(1).reset_camera()

    plotter.at(0).add(transform_vars.usage)
    info_txt = vedo.CornerAnnotation()
    info_txt.text("Nasal Tip Underside Mode")
    plotter.at(1).add(info_txt)

    plotter.add_callback("RightButton", plot_point)
    plotter.add_callback("key press", on_key_press)

    transform_vars.plotter = plotter
    transform_vars.info_txt = info_txt
    transform_vars.select_mode = "nasal_tip"

# Renders a point for a single-point mode
def plot_point(evt):
    select_mode = transform_vars.select_mode
    colour = transform_vars.modes[transform_vars.select_mode].color
    points = [x for x in transform_vars.plotter.actors if x.name == "Point"]

    # Removes pre-existing point if it exists
    for index, point in enumerate(points):
        if all(point.c() == np.array(vedo.colors.get_color(colour))):
            transform_vars.plotter.remove(point)
            transform_vars.plotter.render()

    # Plot new point  
    point = vedo.Point(evt.picked3d).ps(10).c(colour)
    # Ensures that point will render on all devices (vedo issue)
    point.render_points_as_spheres(False)
    transform_vars.plotter.add(point, at=evt.at)
    transform_vars.plotter.render()

    # Replace value in TransformVars
    match evt.at:
        case 0:
            transform_vars.mri_fiducial[select_mode] = point.center_of_mass()
        case 1:
            transform_vars.head_fiducial[select_mode] = point.center_of_mass()
        case _:
            print("Error: add_point unexpected window clicked")

def on_key_press(evt):
    """
    Callback function for vedo Plotter to handle key presses.

    Accepted Keys and functionality:
        Backspace : Delets all points and restores meshes

        Fiducial point modes
        CTRL + N  : Enter Nasion mode or switch back to Helmet mode
        CTRL + L  : Enter LPA mode or switch back to Helmet mode
        CTRL + R  : Enter RPA mode or switch back to Helmet mode

    Parameters
    ----------
    evt : vedo Plotter interaction event.

    Returns
    -------
    None.

    """
    # Clear Input
    if evt.keypress == "BackSpace":
        plotter = transform_vars.plotter
        
        not_point_actors = [
            actor
            for actor in plotter.actors
            if not isinstance(actor, vedo.pointcloud.Points)
        ]
        plotter.actors = not_point_actors

        plotter.at(0).add(transform_vars.mri_mesh)
        plotter.at(0).reset_camera()
        plotter.at(1).add(transform_vars.head_mesh)
        plotter.at(1).reset_camera()

        plotter.at(0).add(transform_vars.usage)
        transform_vars.info_txt.text("Nasal Tip Underside Mode")
        plotter.at(1).add(transform_vars.info_txt)
        transform_vars.select_mode = "nasion_pt"

        # reset lists for point window location, mode/point type and coordinates
        transform_vars.mri_fiducial = {"nasal_tip": None, "lpa_pt": None, "rpa_pt": None}
        transform_vars.head_fiducial = {"nasal_tip": None, "lpa_pt": None, "rpa_pt": None}

        plotter.render()
        return

    modes = transform_vars.modes

    # If the mode entered is already selected, do nothing
    if evt.keypress == modes[transform_vars.select_mode].key:
        return
    # Otherwise, swap to entered mode
    if evt.keypress == modes["nasal_tip"].key:
        transform_vars.info_txt.text(modes["nasal_tip"].text)
        transform_vars.select_mode = modes["nasal_tip"].name

    elif evt.keypress == modes["lpa_pt"].key:
        transform_vars.info_txt.text(modes["lpa_pt"].text)
        transform_vars.select_mode = modes["lpa_pt"].name

    elif evt.keypress == modes["rpa_pt"].key:
        transform_vars.info_txt.text(modes["rpa_pt"].text)
        transform_vars.select_mode = modes["rpa_pt"].name

    # Invalid input
    else:
        return

    # Re-render plotter
    transform_vars.plotter.render()

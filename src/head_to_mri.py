import os
import vedo
import numpy as np
import easygui as eg
from tkinter.filedialog import askopenfilename

import transform_vars
from point_data import process_meshes
from trans_plot_funcs import instantiate_plotter
from point_traversal import find_landmarks

def run():
    path = load_meshes()

    # Loops until user is satisfied with alignment
    while True:
        # Take user input for prearicular points and nasal tip underside
        instantiate_plotter()
        transform_vars.plotter.show(
            title="Press q when done", size="fullscreen"
        ).interactive()
        transform_vars.plotter.render()

        # Crop meshes and find landmarks
        m_mesh, h_mesh = process_meshes()
        mri_landmarks, head_landmarks = find_landmarks(m_mesh, h_mesh)

        # Plotter to show identified landmarks
        landmark_plotter = vedo.Plotter(shape=[1,2], axes=True, bg="blackboard", sharecam=True)
        landmark_plotter.at(0).add(m_mesh.mesh)
        landmark_plotter.at(1).add(h_mesh.mesh)

        # Exclude landmarks that are too different between meshes from transform and plot red
        to_exclude = []
        for index, mri_lmark in enumerate(mri_landmarks):
            head_lmark = head_landmarks[index]
            if np.linalg.norm(mri_lmark - head_lmark) > 0.015:
                to_exclude.append(index)
                colour = "yellow5"
            else:
                colour = "green5"

            # Plot coloured points
            point_m = vedo.Point(mri_lmark).ps(10).c(colour)
            point_m.render_points_as_spheres(False)
            landmark_plotter.at(0).add(point_m)
            point_h = vedo.Point(head_lmark).ps(10).c(colour)
            point_h.render_points_as_spheres(False)
            landmark_plotter.at(1).add(point_h)
        
        landmark_plotter.show(title="Landmark View", size="fullscreen")

        # Remove unusable points from landmark lists
        for index in sorted(to_exclude, reverse=True):
            del mri_landmarks[index]
            del head_landmarks[index]

        # Align head mesh with MRI mesh
        h_mesh.mesh.transform_with_landmarks(head_landmarks, mri_landmarks, rigid=True)

        # Save transform mapping head to mri within fiducial space
        matrix = h_mesh.mesh.get_transform().GetMatrix()
        h_tform = np.empty(shape=(4, 4))
        for i in range(4):
            h_tform[i][0] = matrix.GetElement(i, 0)
            h_tform[i][1] = matrix.GetElement(i, 1)
            h_tform[i][2] = matrix.GetElement(i, 2)
            h_tform[i][3] = matrix.GetElement(i, 3)

        # Reverses transformation of h_mesh so that points appear properly in landmark plotter
        undo = np.linalg.inv(h_tform)
        h_mesh.mesh.apply_transform(undo, reset=True)

        # Apply transformations to original meshes
        final_mri = transform_vars.mri_mesh.clone()
        final_head = transform_vars.head_mesh.clone()
        final_mri.apply_transform(m_mesh.trans_matrix, reset=True)
        final_head.apply_transform(h_mesh.trans_matrix, reset=True)
        final_head.apply_transform(h_tform, reset=True)

        # Plot aligned meshes
        plotter = vedo.Plotter(axes=True, bg="blackboard")
        plotter.add(final_mri, final_head)
        plotter.add(vedo.CornerAnnotation().text("Press Q when done"))
        plotter.show()
         
        # Request user input to decide whether or not to save data
        coreg_complete_choices = ("Yes", "No (Try again)", "Exit")
        coreg_complete_choice = eg.buttonbox(
            msg="Do you want to save this coreg?", choices=coreg_complete_choices
        )

        # Save files if choice is "yes", leaving windows open
        if coreg_complete_choice == coreg_complete_choices[0]:
            np.savetxt(path+"_mri_to_fiducial.tsv", m_mesh.trans_matrix, delimiter='\t')
            np.savetxt(path+"_head_to_fiducial.tsv", h_mesh.trans_matrix, delimiter='\t')
            np.savetxt(path+"_head_fiducial_to_mri.tsv", h_tform, delimiter='\t')
            vedo.file_io.write(final_mri, path+"_alligned_mri.ply")
            vedo.file_io.write(final_head, path+"_alligned_head.ply")
            break

        # Close all plotter objects
        transform_vars.plotter.close()
        transform_vars.plotter.remove()
        landmark_plotter.close()
        landmark_plotter.remove()
        plotter.close()
        plotter.remove()

        # Exit program if choice is "Exit"
        if coreg_complete_choice == coreg_complete_choices[2]:
            break
    
    
# Returns head mesh and MRI mesh, after loading from disk
def load_meshes():
    in_dir = os.path.normpath(os.path.dirname(__file__) + "\\data")

    path = askopenfilename(title="MRI file", initialdir=in_dir)
    mri_mesh = vedo.load(path)
    mri_mesh = check_units(mri_mesh)
    mri_mesh.lighting("default")

    path = askopenfilename(title="Head file", initialdir=in_dir)
    head_mesh = vedo.load(path)
    head_mesh = check_units(head_mesh)
    head_mesh.lighting("default")
    
    transform_vars.mri_mesh = mri_mesh
    transform_vars.head_mesh = head_mesh

    return path[0:-4]

# Checks units of mesh; returns appropriately scaled mesh (in metres)
def check_units(mesh):
    mesh_range = max(mesh.bounds()) - min(mesh.bounds())
    mesh_range_log = np.floor(np.log10(mesh_range))

    # Mesh is in milimetres
    if mesh_range_log >= 2:
        mesh.scale(s=0.001)
    # Mesh is in centimetres
    elif mesh_range_log >= 0.5:
        mesh.scale(s=0.1)

    return mesh

if __name__ == "__main__":
    run()

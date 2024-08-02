import sys
import vedo
import numpy as np
from typing import NamedTuple
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

import transform_vars

# Stores mesh point data for later traversal
class Point(NamedTuple):
    id: int
    coords: list
    connected_points: set

# Stores data relevant to a processed mesh
class ProcessedMesh(NamedTuple):
    mesh: vedo.Mesh
    points: list[Point]
    nasal_tip: Point
    rpa: list[float]
    lpa: list[float]
    trans_matrix: list[list[float]]

# Prepares both meshes for landmark identification
def process_meshes() -> tuple[ProcessedMesh, ProcessedMesh]:
    m_mesh = transform_vars.mri_mesh.clone()
    h_mesh = transform_vars.head_mesh.clone()

    pro_m_mesh = process_mri_mesh(m_mesh, transform_vars.mri_fiducial)
    pro_h_mesh = process_head_mesh(h_mesh, transform_vars.head_fiducial, pro_m_mesh.mesh)

    return pro_m_mesh, pro_h_mesh

# Prepares MRI mesh for alignment
def process_mri_mesh(
    mesh: vedo.Mesh,
    fiducial_points: dict[str, list[float]]
) -> ProcessedMesh:
    trans_mesh, n_tip, lpa, rpa, trans_matrix = transform_mesh_fiducial(mesh, fiducial_points)
    trans_mesh.smooth()

    # Cut below nasal tip
    trans_mesh.cut_with_plane(n_tip, [0,0,1])

    points, nasal_tip = extract_point_data_and_ntip(trans_mesh, n_tip)

    return ProcessedMesh(trans_mesh, points, nasal_tip, rpa, lpa, trans_matrix)

# Prepares head mesh for alignment
def process_head_mesh(
    head_mesh: vedo.Mesh,
    fiducial_points: dict[str, list[float]],
    mri_mesh: vedo.Mesh
) -> ProcessedMesh:
    trans_mesh, n_tip, lpa, rpa, trans_matrix = transform_mesh_fiducial(
        head_mesh, fiducial_points
    )
    # Cut below nasal tip
    trans_mesh.cut_with_plane(n_tip, [0,0,1])
    
    # Find max z for mri mesh - to account for helmet/cap being worn
    mri_coords = vtk_to_numpy(mri_mesh.polydata().GetPoints().GetData())
    max_z = sys.float_info.min
    max_z_coords = []
    for coords in mri_coords:
        if coords[2] > max_z:
            max_z = coords[2]
            max_z_coords = coords
    # Cut above max z
    trans_mesh.cut_with_plane(max_z_coords, [0,0,-1])

    points, nasal_tip = extract_point_data_and_ntip(trans_mesh, n_tip)
    
    return ProcessedMesh(trans_mesh, points, nasal_tip, rpa, lpa, trans_matrix)

# Creates Point objects with their mesh index and coordinates and finds nasal tip
def extract_point_data_and_ntip(
    cropped_mesh: vedo.Mesh, 
    n_coords: list[float]
) -> tuple[list[Point], Point]:
    pd = cropped_mesh.polydata()
    coords = vtk_to_numpy(pd.GetPoints().GetData())
    bounds = cropped_mesh.GetBounds()
    z_range = bounds[5] - bounds[4]
    z_limit = n_coords[2] + z_range/10

    # Set up points and find true nasal tip
    points = []
    nasal_tip_index = 0
    max_x = sys.float_info.min
    for index, coord in enumerate(coords):
        # Nasal tip is point with greatest x within bounds for z
        if coord[0] > max_x and coord[2] < z_limit:
            nasal_tip_index = index
            max_x = coord[0]
        points.append(Point(index, coord, set()))
    points = extract_connection_info(pd, points)

    return points, points[nasal_tip_index]

# Finds connections between each point and adds them to each Point object
def extract_connection_info(point_data, points: list[Point]) -> list[Point]:
    poly_data = point_data.GetPolys().GetData()
    values = [int(poly_data.GetTuple1(i)) for i in range(poly_data.GetNumberOfTuples())]

    # Assumes that polygons are all triangles
    num_triangles = int(len(values) / 4)
    for i in range(num_triangles):
        # Extract Triangle information
        tuple_start = i*4+1
        tuple_end = tuple_start + 3
        triangle_points = values[tuple_start:tuple_end]
        
        # Update Point objects with connections
        point_set = set(triangle_points)
        for point in triangle_points:
            points[point].connected_points.update(point_set.difference([point]))

    return points

# Transforms mesh into desired coordinate space and finds nasal tip
def transform_mesh_fiducial(
    mesh: vedo.Mesh, 
    fiducial_points: dict[str, list[float]]
) -> tuple[vedo.Mesh, list[float], list[float], list[float], list[list[float]]]:
    nasal = fiducial_points["nasal_tip"]
    rpa = fiducial_points["rpa_pt"]
    lpa = fiducial_points["lpa_pt"]
    
    right = rpa - lpa
    right_unit = right / np.linalg.norm(right)
    left_unit = -right_unit

    # Origin falls on the line through nasion and perpendicular to the left-right axis
    origin = lpa + np.dot(nasal - lpa, right_unit) * right_unit

    # Calculate the line perpentidular to the left-right axis
    anterior = nasal - origin
    anterior_unit = anterior / np.linalg.norm(anterior)

    # Calculate direction perpendicular to right and anterior
    superior_unit = np.cross(right_unit, anterior_unit)

    # Translation to the origin
    origin_translation = np.eye(4)
    for i in range(3):
        origin_translation[i,3] = -origin[i]

    rotation_matrix = np.empty([4,4])
    rotation_matrix[0] = np.append(anterior_unit,0)
    rotation_matrix[1] = np.append(left_unit,0)
    rotation_matrix[2] = np.append(superior_unit,0)
    rotation_matrix[3] = [0, 0, 0, 1]

    # Combine two matrices into one transformation matrix
    trans_matrix = np.dot(rotation_matrix, origin_translation)

    # Transform fiducial points and mesh (1 has to be appended to point coord vectors)
    nasal = np.dot(trans_matrix, np.append(nasal,1))[:-1]
    lpa = np.dot(trans_matrix, np.append(lpa,1))[:-1]
    rpa = np.dot(trans_matrix, np.append(rpa,1))[:-1]
    mesh.apply_transform(trans_matrix, reset=True)

    return mesh, nasal, rpa, lpa, trans_matrix

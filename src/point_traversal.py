import vedo
from enum import Enum
from collections import deque

from point_data import Point, ProcessedMesh

# Represents whether x is maximised or minimised during search
class Target(Enum):
    MIN = 1
    MAX = 2

# Returns coordinates of common landmarks in both meshes for plotting and transformation
def find_landmarks(
    mri_mesh: ProcessedMesh, head_mesh: ProcessedMesh
) -> tuple[list[float], list[float]]:
    mri_landmarks = find_non_bridge_landmarks(mri_mesh)
    head_landmarks = find_non_bridge_landmarks(head_mesh)

    # Find common point on nose bridge
    mri_bridge, head_bridge = find_common_nasal_bridge(
        [mri_mesh, head_mesh], [mri_landmarks[0], head_landmarks[0]]
    )
    mri_landmarks.append(mri_bridge)
    head_landmarks.append(head_bridge)

    # Extract coordinates from Point objects
    mri_landmark_coords = list(map(lambda x: x.coords, mri_landmarks))
    mri_landmark_coords.extend([mri_mesh.lpa, mri_mesh.rpa])
    head_landmarks_coords = list(map(lambda x: x.coords, head_landmarks))
    head_landmarks_coords.extend([head_mesh.lpa, head_mesh.rpa])

    return mri_landmark_coords, head_landmarks_coords

def find_non_bridge_landmarks(pro_mesh: ProcessedMesh) -> list[int]:
    points = pro_mesh.points
    bounds = pro_mesh.mesh.GetBounds()
    
    # Extract coordinate range values for mesh
    y_range = bounds[3] - bounds[2]
    z_range = bounds[5] - bounds[4]

    # Find nasion point
    y_bounds, z_bounds = set_bounds(
        pro_mesh.nasal_tip, y_range, z_range, y_min_divisor=110, y_max_divisor=110,
        z_min_divisor=None, z_max_divisor=3.5
        
    )
    # Locate nasion point by minimising x from the nasal tip within the bounds for y and z
    nasion_point = find_point(points, pro_mesh.nasal_tip, Target.MIN, y_bounds, z_bounds)

    # Find left endocanthion
    y_bounds, z_bounds = set_bounds(
        nasion_point, y_range, z_range, y_min_divisor=None, y_max_divisor=20,
        z_min_divisor=10, z_max_divisor=None 
    )
    left_endocanthion = find_point(points, nasion_point, Target.MIN, y_bounds, z_bounds)

    # Find right endocanthion
    y_bounds, z_bounds = set_bounds(
        nasion_point, y_range, z_range, y_min_divisor=20, y_max_divisor=None,
        z_min_divisor=10, z_max_divisor=None
    )
    right_endocanthion = find_point(points, nasion_point, Target.MIN, y_bounds, z_bounds)
    
    # Find forehead point above left endocanthion
    y_bounds, z_bounds = set_bounds(
        left_endocanthion, y_range, z_range, y_min_divisor=100, y_max_divisor=100,
        z_min_divisor=None, z_max_divisor=5
    )
    forehead_left = find_point(points, left_endocanthion, Target.MAX, y_bounds, z_bounds)

    # Find forehead point above right endocanthion
    y_bounds, z_bounds = set_bounds(
        right_endocanthion, y_range, z_range, y_min_divisor=100, y_max_divisor=100,
        z_min_divisor=None, z_max_divisor=5
    )
    forehead_right = find_point(points, right_endocanthion, Target.MAX, y_bounds, z_bounds)

    return [nasion_point, left_endocanthion, right_endocanthion, 
            forehead_left, forehead_right]

# Noses can be warped by MRI: a point guaranteed to be common to both meshes has to be found
def find_common_nasal_bridge(meshes: list[ProcessedMesh], nasions: list[Point]) -> tuple[Point]:
    mri_tip = meshes[0].nasal_tip
    head_tip = meshes[1].nasal_tip
    mri_nasion = nasions[0]
    head_nasion = nasions[1]

    # Find difference in z for nasion and "nasal tip" (to account for pinocchio effect)
    mri_z_diff =  mri_nasion.coords[2] - mri_tip.coords[2]
    head_z_diff = head_nasion.coords[2] - head_tip.coords[2]
    # Use smaller difference as basis for z bounds, in order to find a common bridge point
    if mri_z_diff < head_z_diff:
        z_min = mri_nasion.coords[2] - mri_z_diff/2
    else:
        z_min = head_nasion.coords[2] - head_z_diff/2
    
    nasal_bridge_points = [[], []]
    for index, pro_mesh in enumerate(meshes):
        nasion = nasions[index]
        bounds = pro_mesh.mesh.GetBounds()
        y_range = bounds[3] - bounds[2]

        start_coords = nasion.coords
        y_start = start_coords[1]
        z_start = start_coords[2]
        y_bounds = (y_start-y_range/100, y_start+y_range/100)
        # Use calculated minimum for z
        z_bounds = (z_min, z_start)
        nasal_bridge_points[index] = find_point(
            pro_mesh.points, nasion, Target.MAX, y_bounds, z_bounds
        )

    return (nasal_bridge_points[0], nasal_bridge_points[1])
        
""" 
Used to generate bounds from a given start point, give None for divisor values if no change
from start value is desired. i.e. if the maximum allowed value for y is the start point's
x value, give None as the argument for y_max_divisor; if you want to allow up to an increase of
half the range of y, set it to 2
""" 
def set_bounds(
    start_point: Point,
    y_range: float,
    z_range: float, 
    y_min_divisor: int, 
    y_max_divisor: int,
    z_min_divisor: int,
    z_max_divisor: int
) -> tuple[tuple[float, float], tuple[float, float]]:
    y_start = start_point.coords[1]
    y_sub = y_range/y_min_divisor if y_min_divisor else 0
    y_plus = y_range/y_max_divisor if y_max_divisor else 0
    y_bounds = (y_start-y_sub, y_start+y_plus) 
    
    z_start = start_point.coords[2]
    z_sub = z_range/z_min_divisor if z_min_divisor else 0
    z_plus = z_range/z_max_divisor if z_max_divisor else 0
    z_bounds = (z_start-z_sub, z_start+z_plus)

    return y_bounds, z_bounds

# Finds a point given a start point, a target for x, and bounds for y and z
def find_point(
    points: list[Point],
    start_point: Point, 
    x_target: Target, 
    y_bounds: tuple[float], 
    z_bounds: tuple[float]
) -> Point:
    """ 
    Keep track of indexes of points that are queued, have already been visited or are known to 
    be out of bounds
    """
    queued: set[int] = set()
    visited = {start_point.id}
    out_of_bounds: set[int] = set()

    # Initialise queue based on start_point
    initial_points = start_point.connected_points
    queue = deque(initial_points)
    queued.update(initial_points)

    predicted_point = start_point.id
    best_x = start_point.coords[0]

    # Defines the function used to ascertain whether the current point is an improvement
    match x_target:
        case Target.MIN:
            better = lambda x, y: x < y
        case Target.MAX:
            better = lambda x, y: x > y
    
    point_unnacounted = lambda x: not(x in queued or x in visited or x in out_of_bounds)

    # Loop until queue is empty
    while len(queue) > 0:
        # print(queue)
        # Set current point and remove from queue
        current_point_index = queue.popleft()
        current_point = points[current_point_index]
        queued.remove(current_point_index)
        visited.add(current_point_index)

        if point_in_bounds(current_point, y_bounds, z_bounds):
            # Check for improvement in x
            current_x = current_point.coords[0]
            if better(current_x, best_x):
                best_x = current_x
                predicted_point = current_point_index

            # Add connected points to queue
            to_add = set(filter(point_unnacounted, current_point.connected_points))
            for point in to_add:
                queue.append(point)
                queued.add(point)
        else:
            # Check if connected points should be added to queue
            potential_points = set(filter(point_unnacounted, current_point.connected_points))
            for point in potential_points:
                if point_in_bounds(points[point], y_bounds, z_bounds):
                    queue.append(point)
                    queued.add(point)
                else:
                    out_of_bounds.add(point)

    return points[predicted_point]

def point_in_bounds(point: Point, y_bounds: tuple[float], z_bounds: tuple[float]) -> bool:
    point_coords = point.coords
    y_in_bounds = point_coords[1] >= y_bounds[0] and point_coords[1] <= y_bounds[1]
    z_in_bounds = point_coords[2] >= z_bounds[0] and point_coords[2] <= z_bounds[1]
    
    return y_in_bounds and z_in_bounds


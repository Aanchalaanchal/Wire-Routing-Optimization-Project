import numpy as np
import pyvista as pv
from stl import mesh, main

# Notes
# Everything related to the domain discretization will go in here
# Need to return every x, every y, and every z coordinate
# Need to return vector of all validated points

# Initial mesh processing, receive triangle and bounding box data.
def find_mins_maxs(obj): # Find bottom left and top right coordinates of the bounding box
    # obj is a mesh object
    minx = obj.x.min()
    maxx = obj.x.max()
    miny = obj.y.min()
    maxy = obj.y.max()
    minz = obj.z.min()
    maxz = obj.z.max()
    return minx, maxx, miny, maxy, minz, maxz

def construct_uniform_grid(mesh,sf):
    # mesh is a mesh object from stl 
    minx, maxx, miny, maxy, minz, maxz = find_mins_maxs(mesh)
    SF = sf # 1/SF resolution
    xdim = int((maxx-minx)/SF)
    ydim = int((maxy-miny)/SF)
    zdim = int((maxz-minz)/SF)
    xyz_space = 1*SF
    grid = pv.UniformGrid(
        dims=(xdim, ydim, zdim),
        spacing=(xyz_space,xyz_space,xyz_space),
        origin=(minx, miny, minz),
        )
    return grid # returns a grid object from pyvista

def get_triangles_and_points(mesh,grid):
    triangles = mesh.vectors
    points = grid.points
    return triangles, points
    
# Grid Discretization methods
def write_points_to_file(file,points):
    a_file = open(file, "w")
    for row in points:
        np.savetxt(a_file, [row])
    a_file.close()

def construct_valid_points(triangles,points):
    # triangles = mesh.vectors
    # points = grid.points
    valid_points = np.zeros((len(points))) # will be vector of true/false. Points inside the mesh are true/ outside are false.
    i=0
    for p in points:
        valid_points[i] = not inside(triangles,p)
        i=i+1
    P = points[np.invert(valid_points.astype(bool))]
    return P # P returns an Nx3 array where each row consists of the points outside of the mesh

# triangles is a an array of all the triangles of the mesh, represented by the 3 vertices (i.e 3 xyz coordinate pairs)
def inside(triangles,p):
    # Find the rays in the positive x and y, and negative x and y directions of a point
    # and counts intersections of each ray, if number of intersections = 0 or odd then it is outside

    # Change the bounding box function to this below:
    minx = np.amin(np.amin(triangles, axis = 0), axis = 0)[0]
    maxx = np.amax(np.amax(triangles, axis = 0), axis = 0)[0]
    miny = np.amin(np.amin(triangles, axis = 0), axis = 0)[1]
    maxy = np.amax(np.amax(triangles, axis = 0), axis = 0)[1]
    minz = np.amin(np.amin(triangles, axis = 0), axis = 0)[2]
    maxz = np.amax(np.amax(triangles, axis = 0), axis = 0)[2]
    ray_vec_pos_x = np.array([maxx-minx, 0, 0])
    ray_vec_neg_x = np.array([-(maxx-minx), 0, 0])
    #ray_vec_pos_y = np.array([0, maxy-miny, 0])
    #ray_vec_neg_y = np.array([0, -(maxy-miny), 0])
    ray_vec_neg_z = np.array([0, 0, -(maxz-minz)])
    count_pos_x = 0
    count_neg_x = 0
    #count_pos_y = 0
    #count_neg_y = 0
    count_neg_z = 0
    for triangle in triangles:
        if ray_triangle_intersection(p,ray_vec_pos_x,triangle):
            count_pos_x = count_pos_x+1
        if ray_triangle_intersection(p,ray_vec_neg_x,triangle):
            count_neg_x = count_neg_x+1
        #if ray_triangle_intersection(p,ray_vec_pos_y,triangle):
            #count_pos_y = count_pos_y+1
        #if ray_triangle_intersection(p,ray_vec_neg_y,triangle):
            #count_neg_y = count_neg_y+1
        if ray_triangle_intersection(p,ray_vec_neg_z,triangle):
            count_neg_z = count_neg_z+1
    if count_neg_z == 0:
        return False
    elif count_pos_x == 0 or count_neg_x == 0: #or count_pos_y == 0 or count_neg_y == 0:
        return False
    elif count_pos_x % 2 == 1 or count_neg_x % 2 == 1: #or count_pos_y % 2 == 1 or count_neg_y % 2 == 1:
        return False
    else:
        return True

def ray_triangle_intersection(ray_start, ray_vec, triangle):
    """Moeller–Trumbore intersection algorithm.

        Parameters
        ----------
        ray_start : np.ndarray
            Length three numpy array representing start of point.

        ray_vec : np.ndarray
            Direction of the ray.

        triangle : np.ndarray
            ``3 x 3`` numpy array containing the three vertices of a
            triangle.

        Returns
        -------
        bool
            ``True`` when there is an intersection.

        tuple
            Length three tuple containing the distance ``t``, and the
            intersection in unit triangle ``u``, ``v`` coordinates.  When
            there is no intersection, these values will be:
            ``[np.nan, np.nan, np.nan]``

    """
    v1, v2, v3 = triangle
    eps = 0.000001

    # compute edges
    edge1 = v2 - v1
    edge2 = v3 - v1
    pvec = np.cross(ray_vec, edge2)
    det = edge1.dot(pvec)
    # To understand this view pyvista implementation of the algorithm
    if abs(det) < eps:  # no intersection
        return False

    inv_det = 1.0 / det
    tvec = ray_start - v1
    u = tvec.dot(pvec) * inv_det

    if u < 0.0 or u > 1.0:  # if not intersection
        return False

    qvec = np.cross(tvec, edge1)
    v = ray_vec.dot(qvec) * inv_det

    if v < 0.0 or u + v > 1.0:  # if not intersection
        return False

    t = edge2.dot(qvec) * inv_det
    if t < eps:
        return False

    return True


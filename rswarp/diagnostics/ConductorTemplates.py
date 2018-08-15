import numpy as np
from warp.field_solvers.generateconductors import XPlane, YPlane, ZPlane, Box
from scipy.stats import gaussian_kde


class Conductor(object):

    def __init__(self, top, w3d, conductor):
        self.top = top
        self.conductor = conductor
        self.faces = []
        self.pids = None
        self.center = None
        self.size = None
        self.cbounds = None
        self.x, self.y, self.z = None, None, None
        self.faces = []
        self.pids = self.get_pids()

        if w3d.solvergeom == w3d.XZgeom or w3d.solvergeom == w3d.RZgeom:
            self.axis = [0, 2, 0, 2]
            self.domain = [w3d.xmmin, w3d.zmmin, w3d.xmmax, w3d.zmmax]
            self.cell_size = [w3d.dx, w3d.dz]
        elif w3d.solvergeom == w3d.XYZgeom:
            self.axis = [0, 1, 2, 0, 1, 2]
            self.domain = [w3d.xmmin, w3d.ymmin, w3d.zmmin, w3d.xmmax, w3d.ymmax, w3d.zmmax]
            self.cell_size = [w3d.dx, w3d.dy, w3d.dz]

    def get_pids(self):
        scraped_particles = np.where(self.top.pidlost[:, -1] == self.conductor.condid)

        return scraped_particles

    def _generate_face(self, resolution=100):
        scraped_parts = np.array([self.top.xplost, self.top.yplost, self.top.zplost])
        for bound, axis, face in zip(self.cbounds, self.axis, self.faces):
            x, y = np.meshgrid(np.linspace(self.cbounds[(axis + 1) % 3],
                                           self.cbounds[(axis + 1) % 3 + 3], resolution),
                               np.linspace(self.cbounds[(axis + 2) % 3] * 1e6,
                                           self.cbounds[(axis + 2) % 3 + 3], resolution))
            z = np.ones_like(x) * bound
            positions = np.vstack([x.ravel(), y.ravel()])
            kernel = gaussian_kde(scraped_parts[face, :][:, [(axis + 1) % 3, (axis + 2) % 3]].T * 1e6)
            s = np.reshape(kernel(positions).T, x.shape)
            yield x, y, z, s


class BoxPlot(Conductor):
    def __init__(self, conductor):
        super(Conductor, self).__init__(conductor)
        self.center = conductor.xcent, conductor.ycent, conductor.zcent
        self.size = conductor.xsize, conductor.ysize, conductor.zsize

        xmin, xmax = self.center[0] - self.size[0] / 2., self.center[0] + self.size[0] / 2.
        ymin, ymax = self.center[1] - self.size[1] / 2., self.center[1] + self.size[1] / 2.
        zmin, zmax = self.center[2] - self.size[2] / 2., self.center[2] + self.size[2] / 2.
        mine, maxe = [xmin, ymin, zmin], [xmax, ymax, zmax]
        self.cbounds = np.hstack([mine, maxe])

    def get_particles(self):
        scraped_parts = np.array([self.top.xplost, self.top.yplost, self.top.zplost])

        for bound, axis, cell_size in zip(self.cbounds, self.axis, self.cell_size):
            pof = np.where(np.abs(scraped_parts[:, axis] - bound) <= cell_size)
            self.faces.append(pof[0])

    def generate_box_faces(self):
        for axis, mesh in zip(self.axis, self._generate_face()):
            x, y, z = [mesh[0], mesh[1], mesh[2]][(2 * axis + 2) % 3], \
                      [mesh[0], mesh[1], mesh[2]][(2 * axis + 3) % 3], \
                      [mesh[0], mesh[1], mesh[2]][(2 * axis + 1) % 3]
            s = mesh[3]
            yield x, y, z, s

class XPlanePlot(Conductor):
    def __init__(self, conductor):
        super(Conductor, self).__init__(conductor)


class YPlanePlot(Conductor):
    def __init__(self, conductor):
        super(Conductor, self).__init__(conductor)


class ZPlanePlot(Conductor):
    def __init__(self, conductor):
        super(Conductor, self).__init__(conductor)


conductor_type = {XPlane: XPlanePlot,
                  YPlane: YPlanePlot,
                  ZPlane: ZPlanePlot,
                  Box: BoxPlot}
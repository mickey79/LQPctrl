#coding=utf-8
#author=Joseph Salini
#date=21 april 2011


from abc import ABCMeta, abstractmethod, abstractproperty
from arboris.core import Joint, Frame
from arboris.homogeneousmatrix import ishomogeneousmatrix
from numpy import zeros, array, asarray, dot, arange, ones, vstack, eye


def diff(val1, val2):
    """
    """
    from misc import quatpos
    if ishomogeneousmatrix(asarray(val1)):
        v1 = quatpos(val1)
    else:
        v1 = asarray(val1)
    if ishomogeneousmatrix(asarray(val2)):
        v2 = quatpos(val2)
    else:
        v2 = asarray(val2)
    return v1 - v2



class Ctrl:
    def __init__(self):
        self._error = 0.

    def init(self, world, LQP_ctrl):
        pass

    @abstractmethod
    def update(self, rstate, dt):
        pass

    @property
    def error(self):
        return self._error

################################################################################
#
# dTwist Controllers
#
################################################################################
class dTwistCtrl(Ctrl):
    def __init__(self):
        Ctrl.__init__(self)

    @abstractmethod
    def update(self, pos, vel, rstate, dt):
        pass

class KpCtrl(dTwistCtrl):
    def __init__(self, goal, Kp, Kd=None):
        from numpy import sqrt
        dTwistCtrl.__init__(self)
        self._goal = goal
        self._Kp = Kp
        self._Kd = Kd if Kd is not None else 2*sqrt(Kp)

    def update(self, pos, vel, rstate, dt):
        if isinstance(self._goal, Joint):
            _goal = self._goal.gpos
        elif isinstance(self._goal, Frame):
            _goal = self._goal.pose
        else:
            _goal = self._goal

        self._error = diff(_goal, pos)
        return dot(self._Kp, diff(_goal, pos)) + dot(self._Kd, -vel)


class KpTrajCtrl(dTwistCtrl):
    def __init__(self):
        pass


class QuadraticCtrl(dTwistCtrl):
    def __init__(self, goal, QonR, horizon, dt):
        """ WARNING: THIS CONTROLLER WORKS ONLY IF dt IS CONSTANT!!!!!!
        """
        self._goal = asarray(goal)
        self._QonR = QonR
        self._h    = int(horizon/dt)
        self._dt   = dt

    def _get_quadratic_cmd(self, Px, Pu, QonR, h, x_hat, z_ref):
        from numpy.linalg import inv
        cmd_traj = - dot( inv(dot(Pu.T, Pu) + QonR*eye(h)), dot(Pu.T, dot(Px, x_hat) - z_ref) )
        return cmd_traj


class ZMPCtrl(QuadraticCtrl):
    def __init__(self, zmp_traj, QonR, horizon, dt, cdof):
        QuadraticCtrl.__init__(self, zmp_traj, QonR, horizon, dt)

        self._Px = zeros((self._h, 3))
        self._Pu = zeros((self._h, self._h))
        self._Px[:,0] = 1
        self._Px[:,1] = arange(1, self._h+1)*self._dt
        self._range_N_dt_2_on_2 = (arange(1, self._h+1)*self._dt)**2/2.
        self._temp_Pu = zeros((self._h, self._h))
        for i in range(self._h):
            diag_i = (1 + 3*i + 3*i**2)*dt**3/6
            self._temp_Pu[range(i,self._h), range(self._h-i)] = diag_i

        self._cdof = cdof
        if 0 not in self._cdof: self._up = 0
        elif 1 not in self._cdof: self._up = 1
        elif 2 not in self._cdof: self._up = 2

        self._gravity   = 0.
        self._prev_vel = zeros(3)
        self._counter = 0

    def init(self, world, LQP_ctrl):
        from arboris.controllers import WeightController
        for c in world._controllers:
            if isinstance(c, WeightController):
                self._gravity = abs(c.gravity)

    def _get_com_hat_and_hong(self, pos, vel):
        dvel = (vel - self._prev_vel)/self._dt
        self._prev_vel = vel.copy()
        com_hat = array([pos, vel, dvel])
        com_hat = com_hat[:,self._cdof]

        hong = pos[self._up]/self._gravity

        return com_hat, hong

    def _fit_goal_for_horizon(self):
        goal = self._goal[self._counter:self._counter+self._h]
        self._counter += 1
        if len(goal) < self._h:
            final_value = self._goal[-1].reshape((1, 2))
            len_gap = self._h - len(goal)
            added_part = dot(ones((len_gap,1)), final_value)
            goal = vstack([goal, added_part])
        return goal

    def _update_Px_and_Pu(self, hong):
        #self._Px[:,0] = 1                                  #already computed in __init__
        #self._Px[:,1] = arange(1, self._h+1)*self._dt      #idem
        self._Px[:, 2] = self._range_N_dt_2_on_2 - hong
        self._Pu[:] = self._temp_Pu
        for i in range(self._h):
            self._Pu[range(i,self._h), range(self._h-i)] -= self._dt*hong

    def update(self, pos, vel, rstate, dt):
        assert(abs(dt-self._dt) < 1e-8)

        com_hat, hong = self._get_com_hat_and_hong(pos, vel)
        zmp_ref = self._fit_goal_for_horizon()
        self._update_Px_and_Pu(hong)

        ddV_com_cdof = self._get_quadratic_cmd(self._Px, self._Pu, self._QonR, self._h, com_hat, zmp_ref)
        
        dVcom_des = zeros(3)
        dVcom_des[self._cdof] = com_hat[2,:] + ddV_com_cdof[0] * dt
        return dVcom_des


################################################################################
#
# Wrench Controllers
#
################################################################################
class WrenchCtrl(Ctrl):
    def __init__(self):
        Ctrl.__init__(self)


class ValueCtrl(WrenchCtrl):
    def __init__(self, value):
        WrenchCtrl.__init__(self)

        self._value = asarray(value).flatten()

    def update(self, rstate, dt):
        return self._value


class TrajCtrl(WrenchCtrl):
    def __init__(self):
        WrenchCtrl.__init__(self)




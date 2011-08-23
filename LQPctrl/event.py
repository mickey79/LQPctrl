#coding=utf-8
#author=Joseph Salini
#date=7 july 2011

from arboris.core import NamedObject


common_flags = {}


class Cond:
    """ A class that represents a condition

    Return true if the condition is valid
    """
    def __init__(self):
        pass

    def init(self, world, LQP_ctrl):
        pass

    def update(self, rstate, dt):
        return False



class Exe:
    """ A class that represents an execution

    Normally, this class execute the update method
    if the conditions linked with an Event instance
    are fulfilled
    """
    def __init__(self):
        pass

    def init(self, world, LQP_ctrl):
        pass

    def update(self, rstate, dt, is_cond_fulfilled):
        pass



class Event(NamedObject):
    """ An class Event that links conditions with executions
    """
    def __init__(self, cond, exe, name = None):
        """ An initialization of the Event instance

        inputs:
        cond: a list of conditions, should be Cond instance
        exe: a list of execution, should be Exe instance
        """
        NamedObject.__init__(self, name)
        self.is_active = True
        self._cond_is_fulfilled = False
        if not isinstance(cond, list):
            cond = [cond]
        for c in cond:
            if not isinstance(c, Cond):
                raise TypeError('The elements of the cond list must be Cond instance')
        self.cond = cond
        if not isinstance(exe, list):
            exe = [exe]
        for e in exe:
            if not isinstance(e, Exe):
                raise TypeError('The elements of the exe list must be Exe instance')
        self.exe = exe

    def init(self, world, LQP_ctrl):
        """ An initialization of the Event, to prepare the simulation
        """
#        self.world = world
        for cond in self.cond:
            cond.init(world, LQP_ctrl)
        for exe in self.exe:
            exe.init(world, LQP_ctrl)

    def update(self, rstate, dt, _rec_performance):
        """ Check if the conditions are fulfilled, execute if valid
        """
        if self.is_active:
            self._cond_is_fulfilled = True
            for cond in self.cond:
                self._cond_is_fulfilled &= cond.update(rstate, dt)
        else:
            self._cond_is_fulfilled = False

        # Even if the Event is not active, or the condition are not
        # fulfilled, exe, may be execute (for example if it takes
        # 3 steps to finish its execution.
        for exe in self.exe:
            exe.update(rstate, dt, self._cond_is_fulfilled)

    def cond_is_fulfilled(self):
        return self._cond_is_fulfilled

################################################################################
#                                                                              #
# CONDITIONS                                                                   #
#                                                                              #
################################################################################

class AtTime(Cond):
    def __init__(self, t):
        self.t = t
        self._is_done = False

    def init(self, world, LQP_ctrl):
        self. world = world

    def update(self, rstate, dt):
        if self.world.current_time >= self.t and self._is_done is False:
            self._is_done=True
            return True
        else:
            return False


class IfFlag(Cond):
    def __init__(self, flag_key, status):
        self.flag_key = flag_key
        self.status   = status

    def update(self, rstate, dt):
        if self.flag_key in common_flags:
            if common_flags[self.flag_key] == self.status:
                return True
            else:
                return False
        else:
            return False


class InConvexHull(Cond):
    """
    """
    def __init__(self, frames, point, dof, margin=0., duration=0.):
        self.frames = frames
        self.point_name = point
        self.dof = dof
        self.margin = margin
        self.duration = duration

    def init(self, world, LQP_ctrl):
        """
        """
        self.world = world
        self.LQP_ctrl = LQP_ctrl

    def update(self, rstate, dt):
        """
        """
        from misc import extract_contact_points, convex_hull, is_in_convex_hull, com_properties
        CH = convex_hull(extract_contact_points(self.frames, self.dof))

        if self.point_name in rstate:
            point = rstate[self.point_name]
        elif self.point_name == 'CoM':
            point = com_properties(self.LQP_ctrl.bodies, compute_J=False)
            rstate['CoM'] = point
        if len(point) == 3:
            point = point[self.dof]

        cond_validity = is_in_convex_hull(CH, point, self.margin)
        return cond_validity



################################################################################
#                                                                              #
# EXECUTIONS                                                                   #
#                                                                              #
################################################################################
class Printer(Exe):
    """ A Exe child which print a string if conditions are fulfilled
    """
    def __init__(self, sentence):
        """ An initialization of the Printer instance

        inputs:
        sentence: the string to display
        """
        self.sentence = sentence

    def update(self, rstate, dt, is_cond_fulfilled):
        """ Display the sentence if cond are fulfilled
        """
        if is_cond_fulfilled:
            print self.sentence


class SetFlag(Exe):
    def __init__(self, key, value):
        self.key = key
        self.value   = value
        

    def update(self, rstate, dt, is_cond_fulfilled):
        if is_cond_fulfilled:
            common_flags[self.key] = self.value



class ChangeWeight(Exe):
    """
    """
    def __init__(self, task, ew, duration, sw=None):
        """
        """
        self.task = task
        self._end_weight = ew
        self._start_weight = sw
        self._weight_sequence = []
        self.duration = duration
        self.counter = None
        

    def update(self, rstate, dt, is_cond_fulfilled):
        """
        """
        from misc import interpolate_log
        if is_cond_fulfilled:
            self.counter = 0
            if self._start_weight is None:
                sw = self.task.weight if self.task.weight > 1e-16 else 1e-16
            else:
                sw = self._start_weight if self._start_weight > 1e-16 else 1e-16
            ew = self._end_weight if self._end_weight > 1e-16 else 1e-16
            self._weight_sequence = interpolate_log(sw, ew, self.duration, dt)

        if self.counter is not None:
            if len(self._weight_sequence)>self.counter:
                self.task.set_weight(self._weight_sequence[self.counter])
                self.counter += 1
            else:
                self.counter = None



class ConstActivator(Exe):
    """ Set the activity of a constraint in the Arboris Simulation
    """
    def __init__(self, const, activity=True, in_lqp=False):
        """ An initialization of the ArborisConstActivator instance

        inputs:
        const: a list of constraint, should be arboris.core.Constraint instance
        activity: - True to set the element activity to True
                  - False to set the element activity to False
                  - Anything else to toggle the element activity
        """
        self.const = const
        self.activity = activity
        self.in_lqp = in_lqp
        

    def init(self, world, LQP_ctrl):
        self.LQP_ctrl = LQP_ctrl

    def update(self, rstate, dt, is_cond_fulfilled):
        """ Set the activity of the constraint in the simulation if the conditions are fulfilled
        """
        if is_cond_fulfilled:
            if self.in_lqp is False:
                if self.activity is True:
                    self.const.enable()
                elif self.activity is False:
                    self.const.disable()
            else:
                self.LQP_ctrl.is_enabled[self.const] = self.activity


class DelayFlag(Exe):
    def __init__(self, key, value, delay):
        self.key   = key
        self.value = value
        self.delay = delay
        self._start_time = None

    def init(self, world, LQP_ctrl):
        self.world = world

    def update(self, rstate, dt, is_cond_fulfilled):
        if is_cond_fulfilled:
            self._start_time = self.world.current_time

        if self._start_time is not None and self.world._current_time>=self._start_time+self.delay:
                common_flags[self.key] = self.value
                self._start_time = None


################################################################################
#                                                                              #
# SHORTCUTS                                                                    #
#                                                                              #
################################################################################
SetF = SetFlag
IfF  = IfFlag
DelayF = DelayFlag
InCH = InConvexHull
Prtr  = Printer
ChW   = ChangeWeight
AtT = AtTime
CAct = ConstActivator
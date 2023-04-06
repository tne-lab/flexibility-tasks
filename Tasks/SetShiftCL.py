from collections import OrderedDict
from enum import Enum

import numpy as np

from Components.Both import Both
from Components.BinaryInput import BinaryInput
from Components.Stimmer import Stimmer
from Events.InputEvent import InputEvent
from ..Tasks.SetShift import SetShift


class SetShiftCL(SetShift):
    def __init__(self, *args):
        super(SetShiftCL, self).__init__(*args)
        self.Inputs = Enum('Inputs', [(m.name, m.value) for m in self.Inputs] + [('STIM_CHANGE', 8)])

    @staticmethod
    def get_components():
        comps = super(SetShiftCL, SetShiftCL).get_components()
        comps['bayes'] = [Both]
        comps['stim'] = [Stimmer]
        return comps

    # noinspection PyMethodMayBeStatic
    def get_constants(self):
        constants = super(SetShiftCL, self).get_constants()
        constants['fit'] = False
        constants['delay'] = 3.5
        return constants

    # noinspection PyMethodMayBeStatic
    def get_variables(self):
        variables = super(SetShiftCL, self).get_variables()
        variables['params'] = OrderedDict([('period', 7692), ('amp', 0), ('pw', 100)])
        return variables

    def start(self):
        super(SetShiftCL, self).start()
        self.stim.parametrize(0, [1, 1], self.params['period'], 100000000000000,
                              self.params['amp'] * np.array([[-1, 1], [-1, 1]]), self.params['pw'] * np.array([1, 1]))
        self.stim.start(0)

    def stop(self):
        super(SetShiftCL, self).stop()
        self.bayes.set({'command': 'OptimizeHyper'})
        self.bayes.set({'command': 'Save'})
        self.stim.parametrize(0, [1, 1], self.params['period'], 100, self.params['amp'] * np.array([[-1, 1], [-1, 1]]), self.params['pw'] * np.array([1, 1]))
        self.stim.start(0)

    def handle_input(self):
        super(SetShiftCL, self).handle_input()
        new_params = self.bayes.check()
        if self.state == self.States.INTER_TRIAL_INTERVAL and self.time_in_state() > self.delay and not all(self.params[p] == new_params[p] for p in new_params.keys()):
            self.params.update(new_params)
            self.stim.parametrize(0, [1, 1], self.params['period'], 100000000000000, round(self.params['amp']) * np.array([[-1, 1], [-1, 1]]), self.params['pw'] * np.array([1, 1]))
            self.events.append(InputEvent(self, self.Inputs.STIM_CHANGE, self.params))

    def RESPONSE(self):
        if self.pokes[0] == BinaryInput.ENTERED or self.pokes[2] == BinaryInput.ENTERED:
            if self.cur_trial < self.n_random_start or self.cur_trial >= self.n_random_start + self.correct_to_switch * len(
                    self.rule_sequence):
                self.bayes.set({'command': 'Suggest'})
            else:
                if self.fit:
                    self.bayes.set({'command': 'NewDataFit', 'outcome': self.time_in_state(), 'params': self.params})
                else:
                    self.bayes.set({'command': 'NewData', 'outcome': self.time_in_state(), 'params': self.params})
                    self.bayes.set({'command': 'Suggest'})
        elif self.time_in_state() > self.response_duration:
            self.bayes.set({'command': 'Suggest'})
        super(SetShiftCL, self).RESPONSE()

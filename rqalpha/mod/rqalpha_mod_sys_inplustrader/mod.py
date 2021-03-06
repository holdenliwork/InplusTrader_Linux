# -*- coding: utf-8 -*-

import six

from rqalpha.interface import AbstractMod
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import patch_user_exc
from rqalpha.const import MATCHING_TYPE

from .simulation_broker import SimulationBroker
from .signal_broker import SignalBroker
from .simulation_event_source import SimulationEventSource
from .inplus_data_source import DataSource


class SimulationMod(AbstractMod):
    def __init__(self):
        pass

    def start_up(self, env, mod_config):
        mod_config.matching_type = self.parse_matching_type(mod_config.matching_type)
        if mod_config.commission_multiplier < 0:
            raise patch_user_exc(ValueError(_(u"invalid commission multiplier value: value range is [0, +∞)")))
        if env.config.base.margin_multiplier <= 0:
            raise patch_user_exc(ValueError(_(u"invalid margin multiplier value: value range is (0, +∞]")))

        if env.config.base.frequency == "tick":
            mod_config.volume_limit = False
            if mod_config.matching_type not in [
                MATCHING_TYPE.NEXT_TICK_LAST,
                MATCHING_TYPE.NEXT_TICK_BEST_OWN,
                MATCHING_TYPE.NEXT_TICK_BEST_COUNTERPARTY,
            ]:
                raise RuntimeError(_("Not supported matching type {}").format(mod_config.matching_type))
        else:
            if mod_config.matching_type not in [
                MATCHING_TYPE.NEXT_BAR_OPEN,
                MATCHING_TYPE.CURRENT_BAR_CLOSE,
            ]:
                raise RuntimeError(_("Not supported matching type {}").format(mod_config.matching_type))

        if mod_config.signal:
            env.set_broker(SignalBroker(env, mod_config))
        else:
            env.set_broker(SimulationBroker(env, mod_config))

        event_source = SimulationEventSource(env, env.config.base.account_list)
        env.set_event_source(event_source)

        data_source = DataSource(env.config.mod.sys_inplustrader.mongo)
        env.set_data_source(data_source)


    def tear_down(self, code, exception=None):
        pass

    @staticmethod
    def parse_matching_type(me_str):
        assert isinstance(me_str, six.string_types)
        if me_str == "current_bar":
            return MATCHING_TYPE.CURRENT_BAR_CLOSE
        elif me_str == "next_bar":
            return MATCHING_TYPE.NEXT_BAR_OPEN
        elif me_str == "last":
            return MATCHING_TYPE.NEXT_TICK_LAST
        elif me_str == "best_own":
            return MATCHING_TYPE.NEXT_TICK_BEST_OWN
        elif me_str == "best_counterparty":
            return MATCHING_TYPE.NEXT_TICK_BEST_COUNTERPARTY
        else:
            raise NotImplementedError

from typing import Any

from protocol0.components.action_groups.AbstractActionGroup import AbstractActionGroup
from protocol0.interface.InterfaceState import InterfaceState


class ActionGroupSet(AbstractActionGroup):
    """
    This manager is supposed to group mundane tasks on Live like debug
    or one shot actions on a set (like upgrading to the current naming scheme)
    """

    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(ActionGroupSet, self).__init__(channel=14, filter_active_tracks=False, *a, **k)
        # LOG encoder
        self.add_encoder(identifier=1, name="log current", on_press=self.parent.logManager.log_current)

        # LOGS encoder
        self.add_encoder(identifier=2, name="log set", on_press=self.parent.logManager.log_set)

        # CLR encoder
        self.add_encoder(identifier=3, name="clear logs", on_press=self.parent.logManager.clear)

        # FIX encoder
        self.add_encoder(identifier=4, name="fix", on_press=self.parent.setFixerManager.refresh_set_appearance)

        # PUSH encoder
        self.add_encoder(identifier=5, name="connect push2", on_press=self.parent.push2Manager.connect_push2)

        # RACK encoder
        self.add_encoder(identifier=6, name="update rack devices",
                         on_press=self.parent.setFixerManager.update_audio_effect_racks)

        # TAIL encoder
        self.add_encoder(identifier=11, name="toggle audio clip tails recording", on_press=InterfaceState.toggle_record_audio_clip_tails)

        # MIX encoder
        self.add_encoder(identifier=13, name="scroll all tracks volume", on_scroll=self.parent.trackManager.scroll_all_tracks_volume)

        # VELO encoder
        self.add_encoder(identifier=14, name="scale selected clip velocities", on_scroll=self.parent.clipManager.scale_selected_clip_velocities)

        # RECord encoder
        self.add_encoder(identifier=16, name="bounce session to arrangement", on_press=self.song.bounce_session_to_arrangement)

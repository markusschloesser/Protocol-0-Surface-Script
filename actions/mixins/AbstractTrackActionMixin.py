from abc import abstractmethod
from functools import partial

from typing import TYPE_CHECKING, Callable

from a_protocol_0.utils.decorators import arm_exclusive, only_if_current

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from a_protocol_0.lom.track.AbstractTrack import AbstractTrack


# noinspection PyTypeHints
class AbstractTrackActionMixin(object):
    @arm_exclusive()
    @only_if_current
    def action_arm(self):
        # type: ("AbstractTrack") -> None
        self.action_arm_track() if self.can_be_armed and not self.arm else None

    @abstractmethod
    def action_arm_track(self):
        # type: ("AbstractTrack") -> None
        pass

    @abstractmethod
    def action_unarm(self):
        # type: ("AbstractTrack") -> None
        pass

    @arm_exclusive(auto_arm=True)
    @only_if_current
    def action_sel(self):
        # type: ("AbstractTrack") -> None
        self.parent.application().view.show_view(u'Detail/DeviceChain')
        return self.action_sel_track()

    @abstractmethod
    def action_sel_track(self):
        # type: ("AbstractTrack") -> None
        pass

    def switch_monitoring(self):
        # type: ("AbstractTrack") -> None
        pass

    @arm_exclusive(auto_arm=True)
    def action_restart_and_record(self, action_record_func):
        # type: ("AbstractTrack", Callable) -> None
        """ restart audio to get a count in and recfix"""
        if self.is_recording:
            return self.action_undo()

        self.song.is_playing = False
        self.song.metronome = True
        action_record_func()

        if len(self.song.playing_tracks) > 1:
            self.parent.wait_bars(1, lambda: setattr(self.song, "metronome", False))
        self.parent.wait_bars(self.bar_count + 1, partial(self.action_post_record))

    @abstractmethod
    def action_record_all(self):
        # type: () -> None
        """ this records normally on a simple track and both midi and audio on a group track """
        pass

    @abstractmethod
    def action_post_record(self):
        # type: ("AbstractTrack") -> None
        pass

    @abstractmethod
    def action_record_audio_only(self):
        # type: ("AbstractTrack") -> None
        """
            this records normally on a simple track and only audio on a group track
            is is available on simple tracks just for ease of use
        """
        pass

    @abstractmethod
    def stop(self):
        # type: ("AbstractTrack") -> None
        pass

    def action_undo(self):
        # type: ("AbstractTrack") -> None
        self.parent.clear_tasks()
        self.action_undo_track()

    @abstractmethod
    def action_undo_track(self):
        # type: ("AbstractTrack") -> None
        pass

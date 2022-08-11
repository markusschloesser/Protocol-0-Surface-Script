from typing import Any

from protocol0.domain.lom.clip.Clip import Clip
from protocol0.domain.shared.scheduler.Scheduler import Scheduler
from protocol0.domain.shared.ui.ColorEnum import ColorEnum
from protocol0.shared.logging.Logger import Logger


class AudioClip(Clip):
    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(AudioClip, self).__init__(*a, **k)
        Scheduler.defer(self.appearance.refresh)

    @property
    def file_path(self):
        # type: () -> str
        return self._clip.file_path if self._clip else ""

    def post_record(self, bar_length):
        # type: (int) -> None
        super(AudioClip, self).post_record(bar_length)
        # looping is managed manually by the ext track (in combo with tail clip)
        self.loop.looping = False

    def crop(self):
        # type: () -> None
        """Live.Clip.Clip.crop_sample doesn't exist, so we notify the user"""
        self.appearance.color = ColorEnum.WARNING.color_int_value
        Logger.warning("Please crop %s" % self)

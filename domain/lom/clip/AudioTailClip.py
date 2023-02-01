from functools import partial

from typing import Any

from protocol0.domain.lom.clip.AudioClip import AudioClip
from protocol0.domain.shared.scheduler.Scheduler import Scheduler


class AudioTailClip(AudioClip):
    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(AudioClip, self).__init__(*a, **k)
        Scheduler.defer(partial(setattr, self.loop, "looping", False))

    def fire(self):
        # type: () -> None
        # optimization to be able to play the set at high tempi
        if not self.muted:
            super(AudioTailClip, self).fire()
        else:
            self.muted = False
            Scheduler.defer(super(AudioTailClip, self).fire)

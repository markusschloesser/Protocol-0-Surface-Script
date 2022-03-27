from protocol0.domain.lom.track.TrackColorEnum import TrackColorEnum
from protocol0.domain.lom.track.simple_track.SimpleAudioTrack import SimpleAudioTrack
from protocol0.domain.shared.scheduler.Scheduler import Scheduler


class SimpleInstrumentBusTrack(SimpleAudioTrack):
    DEFAULT_NAME = "Instrument bus"
    DEFAULT_COLOR = TrackColorEnum.DISABLED

    def on_added(self):
        # type: () -> None
        super(SimpleInstrumentBusTrack, self).on_added()
        if len(self.clips):
            self.clips[0].muted = True

    def on_scenes_change(self):
        # type: () -> None
        super(SimpleInstrumentBusTrack, self).on_scenes_change()
        for clip in self.clips[1:]:
            Scheduler.defer(clip.delete)

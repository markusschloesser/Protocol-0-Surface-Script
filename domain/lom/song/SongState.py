from typing import Dict

from protocol0.domain.lom.instrument.instrument.InstrumentSimpler import InstrumentSimpler
from protocol0.domain.lom.instrument.preset.preset_importer.DirectoryPresetImporter import DirectoryPresetImporter
from protocol0.domain.lom.track.TracksMappedEvent import TracksMappedEvent
from protocol0.domain.shared.DomainEventBus import DomainEventBus
from protocol0.domain.shared.backend.Backend import Backend
from protocol0.shared.SongFacade import SongFacade


class SongState(object):
    def __init__(self):
        # type: () -> None
        DomainEventBus.subscribe(TracksMappedEvent, lambda _: self.notify())
        presets = DirectoryPresetImporter(InstrumentSimpler.PRESETS_PATH, InstrumentSimpler.PRESET_EXTENSION).import_presets()
        self.drum_categories = set()
        for preset in presets:
            self.drum_categories.add(preset.category)

    def to_dict(self):
        # type: () -> Dict
        drum_track_names = []
        if SongFacade.drums_track():
            drum_track_names = [track.name for track in SongFacade.drums_track().get_all_simple_sub_tracks()]
        return {
            "track_names": [track.name for track in SongFacade.simple_tracks()],
            "drum_track_names": drum_track_names,
            "drum_categories": list(self.drum_categories)
        }

    def notify(self):
        # type: () -> None
        Backend.client().notify_song_state(self.to_dict())

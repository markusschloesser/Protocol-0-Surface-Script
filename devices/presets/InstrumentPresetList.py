import os
from os.path import isfile, isdir

from typing import TYPE_CHECKING, List, Optional, Any

from protocol0.devices.presets.InstrumentPreset import InstrumentPreset
from protocol0.enums.PresetDisplayOptionEnum import PresetDisplayOptionEnum
from protocol0.lom.AbstractObject import AbstractObject
from protocol0.lom.device.PluginDevice import PluginDevice
from protocol0.lom.device.RackDevice import RackDevice
from protocol0.utils.utils import find_if

if TYPE_CHECKING:
    from protocol0.devices.AbstractInstrument import AbstractInstrument


class InstrumentPresetList(AbstractObject):
    def __init__(self, instrument, *a, **k):
        # type: (AbstractInstrument, Any, Any) -> None
        super(InstrumentPresetList, self).__init__(*a, **k)
        self.instrument = instrument
        self.presets = []  # type: List[InstrumentPreset]
        self.selected_preset = None  # type: Optional[InstrumentPreset]

    def __repr__(self):
        # type: () -> str
        return "preset count: %d, selected preset: %s" % (len(self.presets), self.selected_preset)

    def sync_presets(self):
        # type: () -> None
        self.presets = self._import_presets()
        self.selected_preset = self._get_selected_preset()

    @property
    def categories(self):
        # type: () -> List[str]
        """ overridden """
        return sorted(list(set([preset.category for preset in self.presets if preset.category])))

    @property
    def selected_category(self):
        # type: () -> Optional[str]
        if self.selected_preset:
            return self.selected_preset.category
        else:
            return None

    @selected_category.setter
    def selected_category(self, selected_category):
        # type: (Optional[str]) -> None
        self.selected_preset = self._category_presets(selected_category)[0]

    def _category_presets(self, category=None):
        # type: (Optional[str]) -> List[InstrumentPreset]
        return list(filter(lambda p: p.category == (category or self.selected_category), self.presets))

    def scroll(self, go_next):
        # type: (bool) -> None
        if isinstance(self.instrument.device, RackDevice):
            self.instrument.device.scroll_chain_selector(go_next=go_next)
            self.selected_preset = self.presets[int(self.instrument.device.chain_selector.value)]
            return

        category_presets = self._category_presets()
        if len(category_presets) == 0:
            self.parent.log_warning(
                "Didn't find category presets for cat %s in %s" % (self.selected_category, self.instrument)
            )
            if len(self.categories) == 0:
                self.parent.log_error("Didn't find categories for %s" % self)
                return

            self.selected_category = self.categories[0]
            return self.scroll(go_next=go_next)

        if self.selected_preset and self.selected_category and self.selected_preset.category != self.selected_category:
            new_preset_index = 0
        else:
            offset = category_presets[0].index
            selected_preset_index = self.selected_preset.index if self.selected_preset else 0
            new_preset_index = selected_preset_index + (1 if go_next else -1) - offset

        self.selected_preset = category_presets[new_preset_index % len(category_presets)]

    def _import_presets(self):
        # type: () -> List[InstrumentPreset]
        if not self.instrument.presets_path:
            # Addictive keys or any other multi instrument rack
            if isinstance(self.instrument.device, RackDevice):
                return [
                    self.instrument.make_preset(index=i, name=chain.name)
                    for i, chain in enumerate(self.instrument.device.chains)
                ]
            # Prophet rev2 other vst with accessible presets list
            elif isinstance(self.instrument.device, PluginDevice) and len(self.instrument.device.presets):
                return [
                    self.instrument.make_preset(index=i, name=preset)
                    for i, preset in enumerate(self.instrument.device.presets[0:128])
                ]
        # Serum or any other vst storing presets in a text file
        elif isfile(self.instrument.presets_path):
            return [
                self.instrument.make_preset(index=i, name=name)
                for i, name in enumerate(open(self.instrument.presets_path).readlines()[0:128])
            ]
        # Simpler or Minitaur or any instrument storing presets as files in a directory
        elif isdir(self.instrument.presets_path):
            presets = []
            has_categories = False
            for root, dir_names, files in os.walk(self.instrument.presets_path):
                if len(dir_names):
                    has_categories = True
                if has_categories:
                    if root == self.instrument.presets_path:
                        continue

                    category = root.replace(self.instrument.presets_path + "\\", "").split("\\")[0]
                    for filename in [filename for filename in files if
                                     filename.endswith(self.instrument.PRESET_EXTENSION)]:
                        presets.append(
                            self.instrument.make_preset(index=len(presets), category=category, name=filename))
                else:
                    for filename in [filename for filename in files if
                                     filename.endswith(self.instrument.PRESET_EXTENSION)]:
                        presets.append(self.instrument.make_preset(index=len(presets), name=filename))

            return presets

        self.parent.log_error("Couldn't import presets for %s" % self.instrument)
        return []

    def _get_selected_preset(self):
        # type: () -> Optional[InstrumentPreset]
        """
        Checking first the track name (Serum or Minitaur)
        then the device name (e.g. simpler)
        """
        preset = None

        if len(self.presets) == 0:
            return None

        if self.instrument.device and self.instrument.device.preset_name:
            preset = find_if(lambda p: p.name == self.instrument.device.preset_name, self.presets)
        elif self.instrument.PRESET_DISPLAY_OPTION == PresetDisplayOptionEnum.NAME:
            preset = find_if(lambda p: p.name == self.instrument.track.abstract_track.name, self.presets)

        return preset

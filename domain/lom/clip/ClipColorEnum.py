from protocol0.domain.shared.ui.ColorEnumInterface import ColorEnumInterface
from protocol0.shared.AbstractEnum import AbstractEnum


class ClipColorEnum(ColorEnumInterface, AbstractEnum):
    AUDIO_UN_QUANTIZED = 14
    HAS_AUTOMATION = 28

    @property
    def int_value(self):
        # type: () -> int
        return self.value

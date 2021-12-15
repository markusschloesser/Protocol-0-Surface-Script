from protocol0.enums.AbstractEnum import AbstractEnum


class InputRoutingTypeEnum(AbstractEnum):
    # AUDIO
    ALL_INS = "All Ins"
    REV2_AUX = "REV2_AUX"
    NO_INPUT = "No Input"

    @property
    def label(self):
        # type: () -> str
        return self.value

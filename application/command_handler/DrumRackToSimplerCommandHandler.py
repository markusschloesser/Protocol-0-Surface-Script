from protocol0.application.command.DrumRackToSimplerCommand import DrumRackToSimplerCommand
from protocol0.application.command_handler.CommandHandlerInterface import CommandHandlerInterface
from protocol0.domain.lom.device.DrumRackService import DrumRackService
from protocol0.shared.SongFacade import SongFacade


class DrumRackToSimplerCommandHandler(CommandHandlerInterface):
    def handle(self, _):
        # type: (DrumRackToSimplerCommand) -> None
        self._container.get(DrumRackService).drum_rack_to_simpler(SongFacade.selected_track())

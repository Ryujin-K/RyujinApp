from core.group_imgs.infra import GroupImages
from core.download.domain.download_entity import Chapter
from core.__seedwork.application.use_cases import UseCase


class GroupImgsUseCase(UseCase):
    def execute(self, ch: Chapter, fn=None):
        return GroupImages().run(ch, fn)

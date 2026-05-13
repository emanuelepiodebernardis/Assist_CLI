from pathlib import Path

from assist.schemas.models import Skill


class SkillNotFoundError(Exception):
    """Raised when a skill cannot be found."""


class SkillResolver:
    def __init__(
        self,
        skills_path: str = "assist/skills",
    ) -> None:
        self.skills_path = Path(skills_path)

    def load(
        self,
        skill_names: list[str],
    ) -> list[Skill]:
        loaded_skills = []

        for skill_name in skill_names:
            skill_file = (
                self.skills_path
                / skill_name
                / "SKILL.md"
            )

            if not skill_file.exists():
                raise SkillNotFoundError(
                    f"Skill not found: {skill_name}"
                )

            content = skill_file.read_text(
                encoding="utf-8"
            )

            loaded_skills.append(
                Skill(
                    name=skill_name,
                    content=content,
                )
            )

        return loaded_skills
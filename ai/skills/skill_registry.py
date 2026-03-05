"""
Skill Registry

Manages registration, discovery, and lifecycle of skills.
"""

from typing import Dict, List, Optional, Set
from .base_skill import BaseSkill, SkillCategory
import logging

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Registry for managing skills.

    Provides:
    - Skill registration and unregistration
    - Skill discovery by name, category, or tags
    - Dependency resolution
    - Lifecycle management
    """

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._categories: Dict[SkillCategory, Set[str]] = {}
        self._tags: Dict[str, Set[str]] = {}

    def register(self, skill: BaseSkill) -> None:
        """
        Register a skill.

        Args:
            skill: Skill to register
        """
        skill_name = skill.metadata.name

        if skill_name in self._skills:
            logger.warning(f"Skill '{skill_name}' is already registered. Replacing.")

        # Register skill
        self._skills[skill_name] = skill

        # Index by category
        category = skill.metadata.category
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(skill_name)

        # Index by tags
        for tag in skill.metadata.tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(skill_name)

        logger.info(f"Registered skill: {skill_name}")

    def unregister(self, skill_name: str) -> bool:
        """
        Unregister a skill.

        Args:
            skill_name: Name of skill to unregister

        Returns:
            True if skill was unregistered, False if not found
        """
        if skill_name not in self._skills:
            return False

        skill = self._skills[skill_name]

        # Remove from category index
        self._categories[skill.metadata.category].discard(skill_name)

        # Remove from tag index
        for tag in skill.metadata.tags:
            self._tags[tag].discard(skill_name)

        # Remove skill
        del self._skills[skill_name]

        logger.info(f"Unregistered skill: {skill_name}")
        return True

    def get(self, skill_name: str) -> Optional[BaseSkill]:
        """
        Get a skill by name.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill instance or None if not found
        """
        return self._skills.get(skill_name)

    def get_by_category(self, category: SkillCategory) -> List[BaseSkill]:
        """
        Get all skills in a category.

        Args:
            category: Skill category

        Returns:
            List of skills in the category
        """
        skill_names = self._categories.get(category, set())
        return [self._skills[name] for name in skill_names]

    def get_by_tag(self, tag: str) -> List[BaseSkill]:
        """
        Get all skills with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of skills with the tag
        """
        skill_names = self._tags.get(tag, set())
        return [self._skills[name] for name in skill_names]

    def search(self, query: str) -> List[BaseSkill]:
        """
        Search for skills by name or description.

        Args:
            query: Search query

        Returns:
            List of matching skills
        """
        query_lower = query.lower()
        results = []

        for skill in self._skills.values():
            if (query_lower in skill.metadata.name.lower() or
                query_lower in skill.metadata.description.lower()):
                results.append(skill)

        return results

    def list_all(self) -> List[BaseSkill]:
        """Get all registered skills"""
        return list(self._skills.values())

    def get_dependencies(self, skill_name: str) -> List[str]:
        """
        Get dependencies of a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of dependency skill names
        """
        skill = self.get(skill_name)
        if not skill:
            return []
        return skill.metadata.dependencies

    def resolve_dependencies(self, skill_name: str) -> List[str]:
        """
        Resolve all dependencies recursively.

        Args:
            skill_name: Name of the skill

        Returns:
            List of all dependency skill names in execution order
        """
        visited = set()
        result = []

        def dfs(name: str):
            if name in visited:
                return

            skill = self.get(name)
            if not skill:
                raise ValueError(f"Skill '{name}' not found")

            visited.add(name)

            for dep in skill.metadata.dependencies:
                dfs(dep)

            result.append(name)

        dfs(skill_name)
        return result[:-1]  # Exclude the skill itself

    async def initialize_all(self) -> None:
        """Initialize all registered skills"""
        for skill in self._skills.values():
            await skill.initialize()
        logger.info(f"Initialized {len(self._skills)} skills")

    async def cleanup_all(self) -> None:
        """Cleanup all registered skills"""
        for skill in self._skills.values():
            await skill.cleanup()
        logger.info(f"Cleaned up {len(self._skills)} skills")

    def get_statistics(self) -> Dict:
        """Get registry statistics"""
        return {
            "total_skills": len(self._skills),
            "categories": {
                cat.value: len(skills)
                for cat, skills in self._categories.items()
            },
            "tags": {
                tag: len(skills)
                for tag, skills in self._tags.items()
            },
            "skills": {
                name: skill.get_statistics()
                for name, skill in self._skills.items()
            }
        }

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, skill_name: str) -> bool:
        return skill_name in self._skills

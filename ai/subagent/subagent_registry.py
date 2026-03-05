"""
SubAgent Registry

Manages registration and discovery of sub-agents.
"""

from typing import Dict, List, Optional
from .base_subagent import BaseSubAgent, SubAgentCapability
import logging

logger = logging.getLogger(__name__)


class SubAgentRegistry:
    """
    Registry for managing sub-agents.

    Provides:
    - Agent registration and deregistration
    - Agent discovery by capability
    - Load balancing across agents
    """

    def __init__(self):
        """Initialize the registry"""
        self._agents: Dict[str, BaseSubAgent] = {}
        self._capability_index: Dict[SubAgentCapability, List[str]] = {
            cap: [] for cap in SubAgentCapability
        }

    def register(self, agent: BaseSubAgent) -> None:
        """
        Register a sub-agent.

        Args:
            agent: The sub-agent to register
        """
        if agent.agent_id in self._agents:
            logger.warning(f"Agent {agent.agent_id} already registered, overwriting")

        self._agents[agent.agent_id] = agent

        # Index by capabilities
        for capability in agent.capabilities:
            if agent.agent_id not in self._capability_index[capability]:
                self._capability_index[capability].append(agent.agent_id)

        logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")

    def unregister(self, agent_id: str) -> bool:
        """
        Unregister a sub-agent.

        Args:
            agent_id: ID of the agent to unregister

        Returns:
            True if successful, False if agent not found
        """
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]

        # Remove from capability index
        for capability in agent.capabilities:
            if agent_id in self._capability_index[capability]:
                self._capability_index[capability].remove(agent_id)

        # Remove from main registry
        del self._agents[agent_id]
        logger.info(f"Unregistered agent: {agent.name} ({agent_id})")
        return True

    def get_agent(self, agent_id: str) -> Optional[BaseSubAgent]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)

    def get_agents_by_capability(
        self,
        capability: SubAgentCapability,
        only_available: bool = True
    ) -> List[BaseSubAgent]:
        """
        Get all agents with a specific capability.

        Args:
            capability: The capability to search for
            only_available: If True, only return non-busy agents

        Returns:
            List of matching agents
        """
        agent_ids = self._capability_index.get(capability, [])
        agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]

        if only_available:
            agents = [a for a in agents if not a._is_busy]

        return agents

    def find_best_agent(
        self,
        capability: SubAgentCapability,
        task_type: Optional[str] = None
    ) -> Optional[BaseSubAgent]:
        """
        Find the best available agent for a task.

        Args:
            capability: Required capability
            task_type: Specific task type (optional)

        Returns:
            Best matching agent or None
        """
        agents = self.get_agents_by_capability(capability, only_available=True)

        if not agents:
            # Try to get any agent with capability, even if busy
            agents = self.get_agents_by_capability(capability, only_available=False)

        if not agents:
            return None

        # Filter by task type if specified
        if task_type:
            capable_agents = [a for a in agents if a.can_handle(task_type)]
            if capable_agents:
                agents = capable_agents

        # Simple load balancing: prefer agents with fewer active tasks
        return min(agents, key=lambda a: len(a._active_tasks))

    def get_all_agents(self) -> List[BaseSubAgent]:
        """Get all registered agents"""
        return list(self._agents.values())

    def get_registry_status(self) -> Dict:
        """Get the status of the entire registry"""
        return {
            "total_agents": len(self._agents),
            "agents": [agent.get_status() for agent in self._agents.values()],
            "capabilities": {
                cap.value: len(agent_ids)
                for cap, agent_ids in self._capability_index.items()
            }
        }

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._agents

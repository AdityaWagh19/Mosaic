import numpy as np
import pytest
from simulation.agent import AccentAgent
from simulation.config import SimConfig
from simulation.model import MosaicModel
from simulation.network import make_network


@pytest.fixture
def base_model():
    config = SimConfig(N=10, topology="er", p_er=0.5, seed=42)
    G = make_network(config)
    return MosaicModel(config, G)


def test_interaction_rejected_unchanged(base_model):
    """If distance >= theta, interaction is rejected and accents remain identical."""
    base_model.config.theta = 0.1
    
    agent_listener = base_model.agents_map[0]
    agent_speaker = base_model.agents_map[1]
    
    # Set them far apart
    agent_listener.accent = np.array([0.1]*6)
    agent_speaker.accent = np.array([0.9]*6)
    
    # Save original
    original_listener_accent = agent_listener.accent.copy()
    
    # Attempt update
    accepted = agent_listener.update(agent_speaker)
    
    assert not accepted
    np.testing.assert_array_equal(agent_listener.accent, original_listener_accent)


def test_interaction_accepted_clipping(base_model):
    """If distance < theta, accents update and are clipped to [0, 1]."""
    base_model.config.theta = 3.0  # Allow large interactions
    base_model.config.gamma = 2.0  # Large step
    base_model.config.sigma = 0.5  # Large noise
    
    agent_listener = base_model.agents_map[0]
    agent_speaker = base_model.agents_map[1]
    agent_speaker.centrality = 1.0
    
    agent_listener.accent = np.array([0.0]*6)
    agent_speaker.accent = np.array([1.0]*6)
    
    accepted = agent_listener.update(agent_speaker)
    
    assert accepted
    assert np.all(agent_listener.accent >= 0.0)
    assert np.all(agent_listener.accent <= 1.0)

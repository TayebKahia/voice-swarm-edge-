"""Tests for the swarm controller and the Exp-4 trial.

Two properties carry published claims and are tested hardest: the separation clamp,
which is the entire basis of NFR-12's "zero collisions observed", and the
reproducibility of a trial, since `seed = trial index x 42` is part of the protocol.
"""

from __future__ import annotations

import numpy as np
import pytest

from swarm.control import (CLAMP_DISTANCE, COLLISION_DISTANCE, SHAPES, ControlGains,
                           SwarmController, assign_slots, formation_slots,
                           separation_clamp)
from swarm.env import EnvLimits, NumpyEnv
from swarm.simulate import SEED_MULTIPLIER, TrialSpec, run_trial


class TestFormationSlots:
    @pytest.mark.parametrize("shape", SHAPES)
    def test_returns_one_slot_per_drone(self, shape):
        assert formation_slots(shape, 5).shape == (5, 3)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_every_shape_is_centred_on_its_centroid(self, shape):
        # Otherwise commanding all three about the same point hands one of them a
        # longer approach, which Exp-4's ANOVA would read as a formation effect.
        slots = formation_slots(shape, 5, (1.0, 2.0, 3.0))
        assert np.allclose(slots.mean(axis=0), [1.0, 2.0, 3.0], atol=1e-9)

    @pytest.mark.parametrize("shape", SHAPES)
    def test_slots_are_never_coincident(self, shape):
        slots = formation_slots(shape, 5)
        distance = np.linalg.norm(slots[:, None, :] - slots[None, :, :], axis=2)
        np.fill_diagonal(distance, np.inf)
        assert distance.min() > CLAMP_DISTANCE

    def test_circle_slots_sit_on_the_radius(self):
        slots = formation_slots("circle", 6, (0, 0, 2), radius=4.0)
        assert np.allclose(np.linalg.norm(slots[:, :2], axis=1), 4.0)

    def test_line_slots_are_evenly_spaced(self):
        slots = formation_slots("line", 5, spacing=2.0)
        gaps = np.linalg.norm(np.diff(slots, axis=0), axis=1)
        assert np.allclose(gaps, 2.0)

    def test_heading_rotates_without_changing_the_shape(self):
        a = formation_slots("wedge", 5)
        b = formation_slots("wedge", 5, heading=np.pi / 3)
        pairwise = lambda s: np.sort(np.linalg.norm(s[:, None, :] - s[None, :, :], axis=2).ravel())
        assert np.allclose(pairwise(a), pairwise(b))

    def test_unknown_shape_is_rejected(self):
        with pytest.raises(ValueError, match="unknown shape"):
            formation_slots("spiral", 5)


class TestAssignSlots:
    def test_is_a_permutation(self):
        positions = np.random.default_rng(0).normal(size=(5, 3))
        assert sorted(assign_slots(positions, formation_slots("circle", 5))) == list(range(5))

    def test_beats_greedy_on_a_case_where_greedy_crosses(self):
        # Two drones, two slots, arranged so nearest-first picks the crossing pair.
        positions = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        slots = np.array([[1.1, 0.0, 0.0], [0.1, 0.0, 0.0]])
        assignment = assign_slots(positions, slots)
        cost = sum(np.linalg.norm(positions[i] - slots[assignment[i]]) ** 2 for i in range(2))
        crossing = sum(np.linalg.norm(positions[i] - slots[i]) ** 2 for i in range(2))
        assert cost <= crossing

    def test_identity_when_drones_already_sit_on_slots(self):
        slots = formation_slots("line", 5)
        assert list(assign_slots(slots, slots)) == list(range(5))


class TestSeparationClamp:
    def test_enforces_the_minimum_distance(self):
        positions = np.array([[0.0, 0.0, 2.0], [0.1, 0.0, 2.0]])
        clamped, _, activations = separation_clamp(positions)
        assert np.linalg.norm(clamped[0] - clamped[1]) >= CLAMP_DISTANCE - 1e-6
        assert activations >= 1

    def test_leaves_a_well_separated_swarm_untouched(self):
        positions = formation_slots("circle", 5)
        clamped, _, activations = separation_clamp(positions)
        assert activations == 0
        assert np.allclose(clamped, positions)

    def test_resolves_a_chain_of_three(self):
        # Separating one pair can close another; a single pass is not enough.
        positions = np.array([[0.0, 0, 2], [0.2, 0, 2], [0.4, 0, 2]])
        clamped, _, _ = separation_clamp(positions)
        distance = np.linalg.norm(clamped[:, None, :] - clamped[None, :, :], axis=2)
        np.fill_diagonal(distance, np.inf)
        assert distance.min() >= CLAMP_DISTANCE - 1e-6

    def test_handles_exactly_coincident_drones_deterministically(self):
        positions = np.zeros((2, 3))
        first, _, _ = separation_clamp(positions.copy())
        second, _, _ = separation_clamp(positions.copy())
        assert np.linalg.norm(first[0] - first[1]) >= CLAMP_DISTANCE - 1e-6
        assert np.allclose(first, second)

    def test_cancels_the_approaching_velocity_component(self):
        # Position-only clamping leaves the closing speed intact, so the pair
        # re-penetrates every tick and the clamp fires forever.
        positions = np.array([[0.0, 0, 2], [0.5, 0, 2]])
        velocities = np.array([[1.0, 0, 0], [-1.0, 0, 0]])
        _, clamped_v, _ = separation_clamp(positions, velocities)
        closing = np.dot(clamped_v[0] - clamped_v[1], np.array([1.0, 0, 0]))
        assert closing >= -1e-9

    def test_does_not_touch_a_receding_pair(self):
        positions = np.array([[0.0, 0, 2], [0.5, 0, 2]])
        velocities = np.array([[-1.0, 0, 0], [1.0, 0, 0]])
        _, clamped_v, _ = separation_clamp(positions, velocities)
        assert np.allclose(clamped_v, velocities)


class TestEnv:
    def test_reset_is_reproducible_for_a_seed(self):
        assert np.allclose(NumpyEnv().reset(84)[0], NumpyEnv().reset(84)[0])

    def test_different_seeds_give_different_spawns(self):
        assert not np.allclose(NumpyEnv().reset(1)[0], NumpyEnv().reset(2)[0])

    def test_speed_is_limited_by_norm_not_per_axis(self):
        # Per-component clipping would rotate the commanded vector (ADR-0001).
        env = NumpyEnv(n=1, limits=EnvLimits(max_speed=1.0, max_accel=100.0))
        env.reset(0)
        _, velocities = env.step(np.array([[100.0, 100.0, 0.0]]))
        assert np.linalg.norm(velocities[0]) == pytest.approx(1.0, abs=1e-6)
        assert velocities[0][0] == pytest.approx(velocities[0][1], abs=1e-9)

    def test_drones_do_not_fall_through_the_floor(self):
        env = NumpyEnv(n=1, centroid=(0, 0, 0.1))
        env.reset(0)
        for _ in range(200):
            positions, _ = env.step(np.array([[0.0, 0.0, -10.0]]))
        assert positions[0][2] >= 0.0


class TestController:
    def test_step_before_command_is_an_error(self):
        controller = SwarmController(5, 0.02)
        with pytest.raises(RuntimeError, match="command"):
            controller.step(np.zeros((5, 3)), np.zeros((5, 3)))

    def test_assignment_is_held_not_resolved_every_tick(self):
        # Re-solving lets two drones swap targets on noise and fly through each other.
        controller = SwarmController(5, 0.02)
        positions = np.random.default_rng(3).normal(size=(5, 3))
        controller.command("circle", positions)
        before = controller.targets
        for _ in range(10):
            controller.step(positions, np.zeros((5, 3)))
        assert np.allclose(controller.targets, before)

    def test_separation_pushes_apart_and_is_symmetric(self):
        controller = SwarmController(2, 0.02)
        positions = np.array([[0.0, 0, 2], [0.5, 0, 2]])
        repulsion = controller._separation(positions)
        assert repulsion[0][0] < 0 and repulsion[1][0] > 0
        assert np.allclose(repulsion[0], -repulsion[1])

    def test_no_separation_force_beyond_the_radius(self):
        controller = SwarmController(2, 0.02)
        far = np.array([[0.0, 0, 2], [50.0, 0, 2]])
        assert np.allclose(controller._separation(far), 0.0)


class TestTrial:
    def test_seed_follows_the_published_protocol(self):
        assert TrialSpec(shape="circle", index=7).seed == 7 * SEED_MULTIPLIER

    def test_trial_is_reproducible(self):
        a = run_trial(TrialSpec(shape="circle", index=3, duration_seconds=5.0))
        b = run_trial(TrialSpec(shape="circle", index=3, duration_seconds=5.0))
        assert a.formation_accuracy == b.formation_accuracy
        assert a.convergence_seconds == b.convergence_seconds

    @pytest.mark.parametrize("shape", SHAPES)
    def test_no_collisions_and_the_clamp_holds(self, shape):
        result = run_trial(TrialSpec(shape=shape, index=1, duration_seconds=20.0))
        assert result.collisions == 0
        assert result.min_pair_distance >= COLLISION_DISTANCE

    @pytest.mark.parametrize("shape", SHAPES)
    def test_converges_and_meets_nfr13(self, shape):
        result = run_trial(TrialSpec(shape=shape, index=2, duration_seconds=30.0))
        assert result.converged
        assert result.formation_accuracy >= 0.85

    def test_non_convergence_reports_no_time_rather_than_the_trial_length(self):
        # A trial too short to converge must not read downstream as a slow one.
        result = run_trial(TrialSpec(shape="circle", index=0, duration_seconds=0.2))
        if not result.converged:
            assert result.convergence_seconds is None

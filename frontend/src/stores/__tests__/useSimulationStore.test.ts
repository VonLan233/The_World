import { describe, it, expect, beforeEach } from 'vitest';
import { useSimulationStore } from '../useSimulationStore';
import type { CharacterStateUpdate, ClockState, SimulationEvent, DialogueEvent } from '@shared/types/simulation';

const makeCharState = (id: string): CharacterStateUpdate => ({
  characterId: id,
  needs: { hunger: 80, energy: 70, social: 60, fun: 50, hygiene: 90, comfort: 75 },
  currentActivity: 'idle',
  currentLocation: 'Home',
  mood: 'happy',
  moodScore: 65,
  position: { x: 100, y: 200 },
});

const makeEvent = (id: string, tick: number): SimulationEvent => ({
  id,
  type: 'activity_start',
  characterId: 'c1',
  characterName: 'Alice',
  description: 'Alice started cooking',
  timestamp: Date.now(),
  tick,
  data: {},
});

const makeDialogue = (): DialogueEvent => ({
  id: 'd1',
  speakerId: 'c1',
  speakerName: 'Alice',
  targetId: 'c2',
  targetName: 'Bob',
  dialogue: 'Hello Bob!',
  tierUsed: 'tier3_rules',
  tick: 10,
  timestamp: Date.now(),
  location: 'Town Square',
});

beforeEach(() => {
  useSimulationStore.getState().reset();
});

describe('useSimulationStore', () => {
  describe('updateCharacterState', () => {
    it('adds a new character state', () => {
      const state = makeCharState('c1');
      useSimulationStore.getState().updateCharacterState(state);

      const stored = useSimulationStore.getState().characterStates.get('c1');
      expect(stored).toEqual(state);
    });

    it('updates an existing character state', () => {
      useSimulationStore.getState().updateCharacterState(makeCharState('c1'));

      const updated = { ...makeCharState('c1'), currentActivity: 'cooking' };
      useSimulationStore.getState().updateCharacterState(updated);

      const stored = useSimulationStore.getState().characterStates.get('c1');
      expect(stored?.currentActivity).toBe('cooking');
    });
  });

  describe('addEvent', () => {
    it('adds event to the beginning', () => {
      useSimulationStore.getState().addEvent(makeEvent('e1', 1));
      useSimulationStore.getState().addEvent(makeEvent('e2', 2));

      const events = useSimulationStore.getState().events;
      expect(events[0].id).toBe('e2');
      expect(events[1].id).toBe('e1');
    });

    it('truncates at maxEvents', () => {
      // Set a small max for testing
      useSimulationStore.setState({ maxEvents: 3 });

      for (let i = 0; i < 5; i++) {
        useSimulationStore.getState().addEvent(makeEvent(`e${i}`, i));
      }

      expect(useSimulationStore.getState().events.length).toBe(3);
    });
  });

  describe('setClockState', () => {
    it('updates all clock fields', () => {
      const clock: ClockState = {
        currentTick: 500,
        currentHour: 14,
        currentDay: 3,
        currentSeason: 'summer',
        isPaused: false,
      };
      useSimulationStore.getState().setClockState(clock);

      const s = useSimulationStore.getState();
      expect(s.currentTick).toBe(500);
      expect(s.currentHour).toBe(14);
      expect(s.currentDay).toBe(3);
      expect(s.currentSeason).toBe('summer');
      expect(s.isRunning).toBe(true); // isPaused=false → isRunning=true
    });
  });

  describe('toggleSimulation', () => {
    it('toggles isRunning', () => {
      expect(useSimulationStore.getState().isRunning).toBe(false);
      useSimulationStore.getState().toggleSimulation();
      expect(useSimulationStore.getState().isRunning).toBe(true);
      useSimulationStore.getState().toggleSimulation();
      expect(useSimulationStore.getState().isRunning).toBe(false);
    });
  });

  describe('addDialogue', () => {
    it('adds dialogue to the beginning', () => {
      const d = makeDialogue();
      useSimulationStore.getState().addDialogue(d);

      expect(useSimulationStore.getState().dialogues[0]).toEqual(d);
    });
  });

  describe('reset', () => {
    it('clears all state', () => {
      useSimulationStore.getState().updateCharacterState(makeCharState('c1'));
      useSimulationStore.getState().addEvent(makeEvent('e1', 1));
      useSimulationStore.getState().addDialogue(makeDialogue());
      useSimulationStore.getState().toggleSimulation();

      useSimulationStore.getState().reset();

      const s = useSimulationStore.getState();
      expect(s.characterStates.size).toBe(0);
      expect(s.events.length).toBe(0);
      expect(s.dialogues.length).toBe(0);
      expect(s.isRunning).toBe(false);
    });
  });
});

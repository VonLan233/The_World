import { create } from 'zustand';
import type { SimulationEvent, ClockState, CharacterStateUpdate } from '@shared/types/simulation';

interface SimulationState {
  isRunning: boolean;
  currentTick: number;
  currentHour: number;
  currentDay: number;
  currentSeason: ClockState['currentSeason'];
  characterStates: Map<string, CharacterStateUpdate>;
  events: SimulationEvent[];
  maxEvents: number;
}

interface SimulationActions {
  updateCharacterState: (update: CharacterStateUpdate) => void;
  addEvent: (event: SimulationEvent) => void;
  setClockState: (clock: ClockState) => void;
  toggleSimulation: () => void;
  setRunning: (running: boolean) => void;
  clearEvents: () => void;
  reset: () => void;
}

const initialState: SimulationState = {
  isRunning: false,
  currentTick: 0,
  currentHour: 6,
  currentDay: 1,
  currentSeason: 'spring',
  characterStates: new Map(),
  events: [],
  maxEvents: 200,
};

export const useSimulationStore = create<SimulationState & SimulationActions>((set, get) => ({
  ...initialState,

  updateCharacterState: (update: CharacterStateUpdate) => {
    set((state) => {
      const newMap = new Map(state.characterStates);
      newMap.set(update.characterId, update);
      return { characterStates: newMap };
    });
  },

  addEvent: (event: SimulationEvent) => {
    set((state) => {
      const events = [event, ...state.events];
      // Keep events list bounded
      if (events.length > state.maxEvents) {
        events.length = state.maxEvents;
      }
      return { events };
    });
  },

  setClockState: (clock: ClockState) => {
    set({
      currentTick: clock.currentTick,
      currentHour: clock.currentHour,
      currentDay: clock.currentDay,
      currentSeason: clock.currentSeason,
      isRunning: !clock.isPaused,
    });
  },

  toggleSimulation: () => {
    set((state) => ({ isRunning: !state.isRunning }));
  },

  setRunning: (running: boolean) => {
    set({ isRunning: running });
  },

  clearEvents: () => {
    set({ events: [] });
  },

  reset: () => {
    const { maxEvents } = get();
    set({ ...initialState, maxEvents });
  },
}));

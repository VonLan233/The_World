import type { SimulationEvent, DialogueEvent } from '@shared/types/simulation';
import ChatLog from '@/components/dialogue/ChatLog';
import styles from './SimulationEventLog.module.css';

interface SimulationEventLogProps {
  events: SimulationEvent[];
  dialogues: DialogueEvent[];
}

export default function SimulationEventLog({ events, dialogues }: SimulationEventLogProps) {
  return (
    <div className={styles.eventLog}>
      <div className={styles.panels}>
        <div className={styles.panel}>
          <h4 className={styles.eventLogTitle}>Event Log</h4>
          <div className={styles.eventList}>
            {events.length === 0 ? (
              <p className={styles.eventEmpty}>
                No events yet. Start the simulation to see activity.
              </p>
            ) : (
              events.slice(0, 50).map((event) => (
                <div key={event.id} className={styles.eventItem}>
                  <span className={styles.eventTime}>T{event.tick}</span>
                  <span className={styles.eventChar}>{event.characterName}</span>
                  <span className={styles.eventDesc}>{event.description}</span>
                </div>
              ))
            )}
          </div>
        </div>
        <div className={styles.panel}>
          <ChatLog dialogues={dialogues} />
        </div>
      </div>
    </div>
  );
}

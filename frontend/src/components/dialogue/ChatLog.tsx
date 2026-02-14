import { useEffect, useRef } from 'react';
import type { DialogueEvent } from '@shared/types/simulation';

interface ChatLogProps {
  dialogues: DialogueEvent[];
}

const TIER_COLORS: Record<string, string> = {
  tier1_claude: '#f5a623',
  tier2_ollama: '#5b8def',
  tier3_rules: '#4ecdc4',
};

const TIER_LABELS: Record<string, string> = {
  tier1_claude: 'AI+',
  tier2_ollama: 'AI',
  tier3_rules: 'R',
};

export default function ChatLog({ dialogues }: ChatLogProps) {
  const listRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to top (newest first)
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = 0;
    }
  }, [dialogues.length]);

  return (
    <>
      <h4 style={{
        margin: '0 0 6px 0',
        fontSize: '13px',
        color: '#a0a0b8',
        fontWeight: 600,
      }}>
        Chat Log
      </h4>
      <div
        ref={listRef}
        style={{
          height: 'calc(100% - 24px)',
          overflowY: 'auto',
          fontSize: '12px',
          lineHeight: '1.5',
        }}
      >
        {dialogues.length === 0 ? (
          <p style={{ color: '#666', fontStyle: 'italic', margin: 0 }}>
            No dialogue yet. Characters will talk when they meet.
          </p>
        ) : (
          dialogues.map((d) => (
            <div
              key={d.id}
              style={{
                padding: '3px 0',
                borderBottom: '1px solid rgba(255,255,255,0.05)',
              }}
            >
              <span style={{ color: '#666', marginRight: '6px' }}>
                T{d.tick}
              </span>
              <span
                style={{
                  display: 'inline-block',
                  width: '20px',
                  textAlign: 'center',
                  fontSize: '9px',
                  fontWeight: 700,
                  color: TIER_COLORS[d.tierUsed] ?? '#999',
                  marginRight: '4px',
                }}
                title={d.tierUsed}
              >
                {TIER_LABELS[d.tierUsed] ?? '?'}
              </span>
              <span style={{ color: '#c0a0ff', fontWeight: 600 }}>
                {d.speakerName}
              </span>
              <span style={{ color: '#666', margin: '0 4px' }}>&rarr;</span>
              <span style={{ color: '#80c0ff' }}>
                {d.targetName}
              </span>
              <span style={{ color: '#ccc', marginLeft: '6px' }}>
                &ldquo;{d.dialogue}&rdquo;
              </span>
            </div>
          ))
        )}
      </div>
    </>
  );
}

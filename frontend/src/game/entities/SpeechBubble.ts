import Phaser from 'phaser';

/**
 * A speech bubble that appears above a character sprite.
 * Auto-fades after a configurable duration.
 */
export class SpeechBubble extends Phaser.GameObjects.Container {
  private bg: Phaser.GameObjects.Graphics;
  private label: Phaser.GameObjects.Text;
  private fadeTimer: Phaser.Time.TimerEvent | null = null;

  private static readonly MAX_WIDTH = 200;
  private static readonly PADDING = 8;
  private static readonly ARROW_HEIGHT = 8;
  private static readonly CORNER_RADIUS = 6;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    super(scene, x, y);

    this.bg = scene.add.graphics();
    this.label = scene.add.text(0, 0, '', {
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: '11px',
      color: '#1a1a2e',
      wordWrap: { width: SpeechBubble.MAX_WIDTH - SpeechBubble.PADDING * 2 },
      align: 'left',
    });
    this.label.setOrigin(0.5, 1);

    this.add([this.bg, this.label]);
    this.setDepth(50);
    this.setVisible(false);
  }

  /**
   * Show the bubble with given text, auto-hide after duration ms.
   */
  show(text: string, duration = 4000): void {
    // Cancel previous fade
    if (this.fadeTimer) {
      this.fadeTimer.destroy();
      this.fadeTimer = null;
    }

    this.label.setText(text);

    const textWidth = Math.min(this.label.width, SpeechBubble.MAX_WIDTH - SpeechBubble.PADDING * 2);
    const textHeight = this.label.height;
    const bubbleWidth = textWidth + SpeechBubble.PADDING * 2;
    const bubbleHeight = textHeight + SpeechBubble.PADDING * 2;

    // Position label centered above arrow
    this.label.setPosition(0, -(SpeechBubble.ARROW_HEIGHT));

    // Draw background
    this.bg.clear();
    const left = -bubbleWidth / 2;
    const top = -(SpeechBubble.ARROW_HEIGHT + bubbleHeight);

    // White rounded rect
    this.bg.fillStyle(0xffffff, 0.95);
    this.bg.fillRoundedRect(left, top, bubbleWidth, bubbleHeight, SpeechBubble.CORNER_RADIUS);
    this.bg.lineStyle(1, 0xccccdd, 0.8);
    this.bg.strokeRoundedRect(left, top, bubbleWidth, bubbleHeight, SpeechBubble.CORNER_RADIUS);

    // Triangle pointer
    this.bg.fillStyle(0xffffff, 0.95);
    this.bg.fillTriangle(
      -6, -(SpeechBubble.ARROW_HEIGHT),
      6, -(SpeechBubble.ARROW_HEIGHT),
      0, 0,
    );

    this.setVisible(true);
    this.setAlpha(1);

    // Auto-fade
    this.fadeTimer = this.scene.time.delayedCall(duration, () => {
      this.scene.tweens.add({
        targets: this,
        alpha: 0,
        duration: 500,
        onComplete: () => this.setVisible(false),
      });
    });
  }

  /**
   * Update position to follow a character sprite.
   */
  follow(x: number, y: number): void {
    this.setPosition(x, y - 30); // offset above character circle
  }
}

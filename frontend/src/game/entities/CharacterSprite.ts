import Phaser from 'phaser';

/**
 * Visual representation of a character in the Phaser world.
 * Extends Container to group multiple display objects (avatar circle + name label).
 * Uses tween animation for smooth movement.
 */
export class CharacterSprite extends Phaser.GameObjects.Container {
  private circle: Phaser.GameObjects.Arc;
  private nameLabel: Phaser.GameObjects.Text;
  private moveTween: Phaser.Tweens.Tween | null = null;

  /** Default colors for character circles when no specific color is given */
  private static readonly PALETTE = [
    0x7c5cbf, 0x5b8def, 0x4ecdc4, 0xf5a623, 0xe74c3c,
    0x2ecc71, 0xe91e9c, 0x9b59b6, 0x1abc9c, 0xf39c12,
  ];

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    name: string,
    color?: number,
  ) {
    super(scene, x, y);

    // Determine color: use provided or derive from name hash
    const resolvedColor = color ?? this.colorFromName(name);

    // Avatar circle (placeholder for future sprite/image)
    this.circle = scene.add.circle(0, 0, 14, resolvedColor, 1);
    this.circle.setStrokeStyle(2, 0xe4e4ef, 0.8);

    // Inner highlight for depth
    const highlight = scene.add.circle(-3, -3, 4, 0xffffff, 0.25);

    // Character name label
    this.nameLabel = scene.add.text(0, 22, name, {
      fontFamily: 'Inter, system-ui, sans-serif',
      fontSize: '11px',
      color: '#e4e4ef',
      align: 'center',
      stroke: '#0f0f13',
      strokeThickness: 3,
    });
    this.nameLabel.setOrigin(0.5, 0);

    // Add children to container
    this.add([this.circle, highlight, this.nameLabel]);

    // Set depth so characters render above the grid
    this.setDepth(10);

    // Entrance animation
    this.setScale(0);
    scene.tweens.add({
      targets: this,
      scaleX: 1,
      scaleY: 1,
      duration: 300,
      ease: 'Back.easeOut',
    });
  }

  /**
   * Smoothly move the character to a new position using tweens.
   */
  moveTo(targetX: number, targetY: number): void {
    // Cancel any in-progress movement
    if (this.moveTween && this.moveTween.isPlaying()) {
      this.moveTween.stop();
    }

    const distance = Phaser.Math.Distance.Between(this.x, this.y, targetX, targetY);
    // Duration scales with distance, min 200ms, max 2000ms
    const duration = Phaser.Math.Clamp(distance * 3, 200, 2000);

    this.moveTween = this.scene.tweens.add({
      targets: this,
      x: targetX,
      y: targetY,
      duration,
      ease: 'Quad.easeInOut',
    });
  }

  /**
   * Update the displayed name.
   */
  setName(name: string): void {
    this.nameLabel.setText(name);
  }

  /**
   * Update the circle color.
   */
  setColor(color: number): void {
    this.circle.setFillStyle(color, 1);
  }

  /**
   * Derive a consistent color from a character name string.
   */
  private colorFromName(name: string): number {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % CharacterSprite.PALETTE.length;
    return CharacterSprite.PALETTE[index];
  }
}

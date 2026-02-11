import Phaser from 'phaser';

/**
 * Boot scene: displays a loading indicator and transitions to WorldScene.
 * In the future, this scene will handle asset preloading.
 */
export class BootScene extends Phaser.Scene {
  private loadingText!: Phaser.GameObjects.Text;

  constructor() {
    super({ key: 'BootScene' });
  }

  preload(): void {
    // Display loading text
    const { width, height } = this.cameras.main;

    this.loadingText = this.add
      .text(width / 2, height / 2, 'Loading...', {
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: '28px',
        color: '#e4e4ef',
      })
      .setOrigin(0.5, 0.5);

    // Pulsing animation for the loading text
    this.tweens.add({
      targets: this.loadingText,
      alpha: { from: 1, to: 0.3 },
      duration: 800,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    });

    // TODO: Load sprite sheets, tile maps, audio, etc.
    // this.load.spritesheet('character', 'assets/character.png', { ... });
    // this.load.image('tiles', 'assets/tiles.png');
    // this.load.tilemapTiledJSON('world-map', 'assets/world.json');

    // Simulate a brief loading delay for UX
    this.load.on('complete', () => {
      this.time.delayedCall(500, () => {
        this.transitionToWorld();
      });
    });
  }

  create(): void {
    // If there were no assets to load, preload's 'complete' won't fire
    // after create, so we handle immediate transition here.
    if (this.load.totalComplete === this.load.totalToLoad) {
      this.time.delayedCall(500, () => {
        this.transitionToWorld();
      });
    }
  }

  private transitionToWorld(): void {
    this.loadingText.destroy();
    this.scene.start('WorldScene');
  }
}

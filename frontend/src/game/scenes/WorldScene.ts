import Phaser from 'phaser';
import { EventBus, GameEvents } from '../EventBus';
import { CharacterSprite } from '../entities/CharacterSprite';

interface AddCharacterData {
  id: string;
  name: string;
  x: number;
  y: number;
  color?: number;
}

interface MoveCharacterData {
  id: string;
  x: number;
  y: number;
}

/**
 * Main world/simulation scene.
 * Renders the world grid, manages character sprites,
 * and communicates with React via EventBus.
 */
export class WorldScene extends Phaser.Scene {
  private characterSprites: Map<string, CharacterSprite> = new Map();
  private gridGraphics!: Phaser.GameObjects.Graphics;

  // World dimensions in pixels
  private worldWidth = 2048;
  private worldHeight = 1536;
  private tileSize = 32;

  constructor() {
    super({ key: 'WorldScene' });
  }

  create(): void {
    this.createGrid();
    this.createUI();
    this.setupCamera();
    this.setupEventListeners();

    // Notify React that the scene is ready
    EventBus.emit(GameEvents.SCENE_READY, this);
  }

  update(_time: number, _delta: number): void {
    // Future: update character animations, particles, etc.
  }

  // -- Setup --

  private createGrid(): void {
    this.gridGraphics = this.add.graphics();
    this.gridGraphics.lineStyle(1, 0x1a1a24, 0.5);

    // Draw vertical lines
    for (let x = 0; x <= this.worldWidth; x += this.tileSize) {
      this.gridGraphics.lineBetween(x, 0, x, this.worldHeight);
    }

    // Draw horizontal lines
    for (let y = 0; y <= this.worldHeight; y += this.tileSize) {
      this.gridGraphics.lineBetween(0, y, this.worldWidth, y);
    }

    // Draw a subtle border around the world
    this.gridGraphics.lineStyle(2, 0x2e2e42, 0.8);
    this.gridGraphics.strokeRect(0, 0, this.worldWidth, this.worldHeight);

    // Background fill
    const bg = this.add.rectangle(
      this.worldWidth / 2,
      this.worldHeight / 2,
      this.worldWidth,
      this.worldHeight,
      0x0f0f13,
    );
    bg.setDepth(-10);

    // Add some placeholder location zones
    this.createLocationZone(200, 200, 192, 128, 'Home', 0x7c5cbf);
    this.createLocationZone(600, 300, 256, 160, 'Park', 0x4ecdc4);
    this.createLocationZone(1000, 200, 192, 128, 'Cafe', 0xf5a623);
    this.createLocationZone(400, 700, 224, 160, 'Library', 0x5b8def);
    this.createLocationZone(1200, 600, 192, 128, 'Gym', 0xe74c3c);
  }

  private createLocationZone(
    x: number,
    y: number,
    width: number,
    height: number,
    label: string,
    color: number,
  ): void {
    // Semi-transparent zone rectangle
    const zone = this.add.rectangle(x, y, width, height, color, 0.15);
    zone.setStrokeStyle(2, color, 0.6);
    zone.setDepth(-5);

    // Zone label
    this.add
      .text(x, y - height / 2 + 14, label, {
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: '14px',
        color: `#${color.toString(16).padStart(6, '0')}`,
        fontStyle: 'bold',
      })
      .setOrigin(0.5, 0.5)
      .setDepth(-4);
  }

  private createUI(): void {
    // Title overlay (fixed to camera)
    this.add
      .text(16, 16, 'The World - Simulation View', {
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: '18px',
        color: '#a0a0b8',
        backgroundColor: '#0f0f13cc',
        padding: { x: 12, y: 8 },
      })
      .setScrollFactor(0)
      .setDepth(100);
  }

  private setupCamera(): void {
    const cam = this.cameras.main;
    cam.setBounds(0, 0, this.worldWidth, this.worldHeight);
    cam.setZoom(1);
    cam.centerOn(this.worldWidth / 2, this.worldHeight / 2);

    // Enable camera drag with middle mouse or pointer
    this.input.on('pointermove', (pointer: Phaser.Input.Pointer) => {
      if (pointer.isDown && (pointer.button === 1 || pointer.event.shiftKey)) {
        cam.scrollX -= (pointer.x - pointer.prevPosition.x) / cam.zoom;
        cam.scrollY -= (pointer.y - pointer.prevPosition.y) / cam.zoom;
      }
    });

    // Zoom with scroll wheel
    this.input.on('wheel', (_pointer: Phaser.Input.Pointer, _gx: number[], _gy: number[], _gz: number[], _gw: number, _gh: number, event: WheelEvent) => {
      const zoomDelta = event.deltaY > 0 ? -0.1 : 0.1;
      const newZoom = Phaser.Math.Clamp(cam.zoom + zoomDelta, 0.5, 3);
      cam.setZoom(newZoom);
    });
  }

  private setupEventListeners(): void {
    // React -> Phaser: Add a character sprite
    EventBus.on(
      GameEvents.ADD_CHARACTER,
      (data: AddCharacterData) => {
        this.addCharacterSprite(data);
      },
      this,
    );

    // React -> Phaser: Move a character sprite
    EventBus.on(
      GameEvents.MOVE_CHARACTER,
      (data: MoveCharacterData) => {
        const sprite = this.characterSprites.get(data.id);
        if (sprite) {
          sprite.moveToPosition(data.x, data.y);
        }
      },
      this,
    );

    // React -> Phaser: Remove a character sprite
    EventBus.on(
      GameEvents.REMOVE_CHARACTER,
      (data: { id: string }) => {
        this.removeCharacterSprite(data.id);
      },
      this,
    );

    // Clean up listeners when scene shuts down
    this.events.on('shutdown', () => {
      EventBus.off(GameEvents.ADD_CHARACTER);
      EventBus.off(GameEvents.MOVE_CHARACTER);
      EventBus.off(GameEvents.REMOVE_CHARACTER);
    });
  }

  // -- Character management --

  private addCharacterSprite(data: AddCharacterData): void {
    if (this.characterSprites.has(data.id)) {
      // Already exists, just move it
      const existing = this.characterSprites.get(data.id)!;
      existing.moveToPosition(data.x, data.y);
      return;
    }

    const sprite = new CharacterSprite(this, data.x, data.y, data.name, data.color);
    this.add.existing(sprite as unknown as Phaser.GameObjects.GameObject);
    this.characterSprites.set(data.id, sprite);

    // Click handler
    sprite.setInteractive(
      new Phaser.Geom.Circle(0, 0, 16),
      Phaser.Geom.Circle.Contains,
    );
    sprite.on('pointerdown', () => {
      EventBus.emit(GameEvents.CHARACTER_CLICKED, { id: data.id, name: data.name });
    });
  }

  private removeCharacterSprite(id: string): void {
    const sprite = this.characterSprites.get(id);
    if (sprite) {
      sprite.destroy();
      this.characterSprites.delete(id);
    }
  }
}

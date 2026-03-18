import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import apiClient from '@/api/client';
import styles from './WorldSetupPage.module.css';

interface WorldData {
  id: string;
  name: string;
  description: string | null;
  lore: string | null;
  map_url: string | null;
  ai_settings_configured: boolean;
}

interface AiConfig {
  text_provider: string;
  text_api_key: string;
  text_model: string;
  image_provider: string;
  image_api_key: string;
}

type MapTab = 'upload' | 'generate';

export default function WorldSetupPage() {
  const { worldId } = useParams<{ worldId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const characterId = (location.state as { characterId?: string } | null)?.characterId ?? null;

  const [world, setWorld] = useState<WorldData | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [lore, setLore] = useState('');
  const [mapUrl, setMapUrl] = useState<string | null>(null);
  const [mapTab, setMapTab] = useState<MapTab>('upload');
  const [mapPrompt, setMapPrompt] = useState('');
  const [lorePrompt, setLorePrompt] = useState('');
  const [aiConfig, setAiConfig] = useState<AiConfig>({
    text_provider: '',
    text_api_key: '',
    text_model: '',
    image_provider: 'openai',
    image_api_key: '',
  });
  const [aiOpen, setAiOpen] = useState(false);

  const [saving, setSaving] = useState(false);
  const [generatingLore, setGeneratingLore] = useState(false);
  const [generatingMap, setGeneratingMap] = useState(false);
  const [uploadingMap, setUploadingMap] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'ok' | 'err' | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load world on mount
  useEffect(() => {
    if (!worldId) return;
    apiClient.get<WorldData>(`/worlds/${worldId}`).then((res) => {
      const w = res.data;
      setWorld(w);
      setName(w.name);
      setDescription(w.description ?? '');
      setLore(w.lore ?? '');
      setMapUrl(w.map_url ? `${w.map_url}?t=${Date.now()}` : null);
    }).catch(() => {});
  }, [worldId]);

  const handleSaveBasic = async () => {
    if (!worldId) return;
    setSaving(true);
    setSaveStatus(null);
    try {
      await apiClient.patch(`/worlds/${worldId}`, { name, description, lore });
      setSaveStatus('ok');
    } catch {
      setSaveStatus('err');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAiConfig = async () => {
    if (!worldId) return;
    setSaving(true);
    setSaveStatus(null);
    try {
      const payload: Record<string, string> = {};
      if (aiConfig.text_provider) payload.text_provider = aiConfig.text_provider;
      if (aiConfig.text_api_key) payload.text_api_key = aiConfig.text_api_key;
      if (aiConfig.text_model) payload.text_model = aiConfig.text_model;
      if (aiConfig.image_provider) payload.image_provider = aiConfig.image_provider;
      if (aiConfig.image_api_key) payload.image_api_key = aiConfig.image_api_key;
      await apiClient.patch(`/worlds/${worldId}`, { ai_settings: payload });
      setSaveStatus('ok');
    } catch {
      setSaveStatus('err');
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateLore = async () => {
    if (!worldId || !lorePrompt.trim()) return;
    setGeneratingLore(true);
    try {
      const res = await apiClient.post<{ lore: string }>(`/worlds/${worldId}/lore/generate`, {
        prompt: lorePrompt,
      });
      setLore(res.data.lore);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Lore generation failed: ${msg ?? 'Unknown error'}`);
    } finally {
      setGeneratingLore(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !worldId) return;
    setUploadingMap(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await apiClient.post<WorldData>(`/worlds/${worldId}/map/upload`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMapUrl(res.data.map_url ? `${res.data.map_url}?t=${Date.now()}` : null);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Upload failed: ${msg ?? 'Unknown error'}`);
    } finally {
      setUploadingMap(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleGenerateMap = async () => {
    if (!worldId) return;
    setGeneratingMap(true);
    try {
      const res = await apiClient.post<WorldData>(`/worlds/${worldId}/map/generate`, {
        prompt: mapPrompt || `A fantasy world map for "${name}"`,
      });
      setMapUrl(res.data.map_url ? `${res.data.map_url}?t=${Date.now()}` : null);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(`Map generation failed: ${msg ?? 'Unknown error'}`);
    } finally {
      setGeneratingMap(false);
    }
  };

  const handleEnterWorld = async () => {
    // Save everything first
    if (!worldId) return;
    setSaving(true);
    try {
      await apiClient.patch(`/worlds/${worldId}`, { name, description, lore });
    } catch { /* ignore */ }
    setSaving(false);
    navigate(`/world/${worldId}`, { state: { characterId } });
  };

  const backendBase = window.location.origin;
  const fullMapUrl = mapUrl?.startsWith('/') ? `${backendBase}${mapUrl}` : mapUrl;

  if (!world) {
    return (
      <div className={styles.page}>
        <div className={styles.container}>
          <p style={{ color: 'var(--color-text-secondary)' }}>Loading world...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        {/* Header */}
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>World Setup</h1>
            <p className={styles.subtitle}>Configure your world before entering the simulation.</p>
          </div>
          <button className={styles.btnEnter} onClick={handleEnterWorld} disabled={saving}>
            {saving ? <span className={styles.spinner} /> : null}
            Enter World
          </button>
        </div>

        {/* Basic Info */}
        <section className={styles.card}>
          <h2 className={styles.cardTitle}>Basic Information</h2>
          <div className={styles.field}>
            <label className={styles.label}>World Name</label>
            <input
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My World"
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Description</label>
            <textarea
              className={styles.textarea}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="A brief description of this world..."
              rows={3}
            />
          </div>
          <div className={styles.btnRow}>
            <button className={styles.btnPrimary} onClick={handleSaveBasic} disabled={saving}>
              {saving ? <span className={styles.spinner} /> : null}
              Save
            </button>
            {saveStatus === 'ok' && <span className={styles.statusOk}>Saved</span>}
            {saveStatus === 'err' && <span className={styles.statusErr}>Save failed</span>}
          </div>
        </section>

        {/* Lore */}
        <section className={styles.card}>
          <h2 className={styles.cardTitle}>World Lore</h2>
          <div className={styles.field}>
            <label className={styles.label}>Lore / World Bible</label>
            <textarea
              className={styles.textarea}
              value={lore}
              onChange={(e) => setLore(e.target.value)}
              placeholder="Write your world's history, rules, factions, magic system..."
              rows={8}
              style={{ minHeight: 200 }}
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>AI Generation Prompt</label>
            <textarea
              className={styles.textarea}
              value={lorePrompt}
              onChange={(e) => setLorePrompt(e.target.value)}
              placeholder="Describe the world you want: genres, themes, tone..."
              rows={3}
            />
          </div>
          <div className={styles.btnRow}>
            <button
              className={styles.btnSecondary}
              onClick={handleGenerateLore}
              disabled={generatingLore || !lorePrompt.trim()}
            >
              {generatingLore ? <span className={styles.spinner} style={{ borderTopColor: 'var(--color-accent-primary)', borderColor: 'var(--color-border)' }} /> : null}
              AI Generate Lore
            </button>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
              Requires text API key below
            </span>
          </div>
        </section>

        {/* Map */}
        <section className={styles.card}>
          <h2 className={styles.cardTitle}>World Map</h2>
          <div className={styles.tabs}>
            <button
              className={`${styles.tab} ${mapTab === 'upload' ? styles.tabActive : ''}`}
              onClick={() => setMapTab('upload')}
            >
              Upload Image
            </button>
            <button
              className={`${styles.tab} ${mapTab === 'generate' ? styles.tabActive : ''}`}
              onClick={() => setMapTab('generate')}
            >
              AI Generate
            </button>
          </div>

          {mapTab === 'upload' && (
            <>
              <div
                className={styles.dropzone}
                onClick={() => fileInputRef.current?.click()}
              >
                {uploadingMap
                  ? 'Uploading...'
                  : 'Click to select an image (JPG, PNG, WebP — max 10 MB)'}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
              />
            </>
          )}

          {mapTab === 'generate' && (
            <div className={styles.field}>
              <label className={styles.label}>Image Prompt</label>
              <textarea
                className={styles.textarea}
                value={mapPrompt}
                onChange={(e) => setMapPrompt(e.target.value)}
                placeholder="A bird's-eye view fantasy world map with forests, mountains, and a central city..."
                rows={3}
              />
              <button
                className={styles.btnSecondary}
                onClick={handleGenerateMap}
                disabled={generatingMap}
                style={{ alignSelf: 'flex-start' }}
              >
                {generatingMap ? <span className={styles.spinner} style={{ borderTopColor: 'var(--color-accent-primary)', borderColor: 'var(--color-border)' }} /> : null}
                Generate Map (DALL-E)
              </button>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
                Requires image API key below
              </span>
            </div>
          )}

          {fullMapUrl && (
            <img src={fullMapUrl} alt="World map preview" className={styles.mapPreview} />
          )}
        </section>

        {/* AI Configuration */}
        <section className={styles.card}>
          <div
            className={styles.collapsibleHeader}
            onClick={() => setAiOpen((o) => !o)}
          >
            <h2 className={styles.cardTitle} style={{ margin: 0 }}>AI Configuration</h2>
            <span className={`${styles.collapsibleChevron} ${aiOpen ? styles.collapsibleChevronOpen : ''}`}>
              ▾
            </span>
          </div>

          {aiOpen && (
            <div className={styles.collapsibleBody}>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', margin: 0 }}>
                Configure your own AI API keys. These override the server defaults and are stored
                encrypted at rest. Keys are never exposed to the client after saving.
              </p>

              <div className={styles.field}>
                <label className={styles.label}>Text Provider</label>
                <select
                  className={styles.select}
                  value={aiConfig.text_provider}
                  onChange={(e) => setAiConfig((c) => ({ ...c, text_provider: e.target.value }))}
                >
                  <option value="">Use server default</option>
                  <option value="anthropic">Anthropic (Claude)</option>
                  <option value="openai">OpenAI (GPT)</option>
                </select>
              </div>

              {aiConfig.text_provider && (
                <>
                  <div className={styles.field}>
                    <label className={styles.label}>
                      {aiConfig.text_provider === 'anthropic' ? 'Anthropic' : 'OpenAI'} API Key
                    </label>
                    <input
                      type="password"
                      className={styles.input}
                      value={aiConfig.text_api_key}
                      onChange={(e) => setAiConfig((c) => ({ ...c, text_api_key: e.target.value }))}
                      placeholder="sk-..."
                      autoComplete="off"
                    />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>
                      Model (optional — leave blank for default)
                    </label>
                    <input
                      className={styles.input}
                      value={aiConfig.text_model}
                      onChange={(e) => setAiConfig((c) => ({ ...c, text_model: e.target.value }))}
                      placeholder={
                        aiConfig.text_provider === 'anthropic'
                          ? 'claude-sonnet-4-6'
                          : 'gpt-4o'
                      }
                    />
                  </div>
                </>
              )}

              <div className={styles.field}>
                <label className={styles.label}>Image Provider (for map generation)</label>
                <select
                  className={styles.select}
                  value={aiConfig.image_provider}
                  onChange={(e) => setAiConfig((c) => ({ ...c, image_provider: e.target.value }))}
                >
                  <option value="openai">OpenAI (DALL-E 3)</option>
                </select>
              </div>

              <div className={styles.field}>
                <label className={styles.label}>Image API Key (OpenAI)</label>
                <input
                  type="password"
                  className={styles.input}
                  value={aiConfig.image_api_key}
                  onChange={(e) => setAiConfig((c) => ({ ...c, image_api_key: e.target.value }))}
                  placeholder="sk-..."
                  autoComplete="off"
                />
              </div>

              <div className={styles.btnRow}>
                <button className={styles.btnPrimary} onClick={handleSaveAiConfig} disabled={saving}>
                  {saving ? <span className={styles.spinner} /> : null}
                  Save AI Config
                </button>
                {saveStatus === 'ok' && <span className={styles.statusOk}>Saved</span>}
                {saveStatus === 'err' && <span className={styles.statusErr}>Save failed</span>}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

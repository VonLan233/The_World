import { useState, useCallback, type FormEvent, type KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCharacterStore } from '@/stores/useCharacterStore';
import { useAuthStore } from '@/stores/useAuthStore';
import type { CharacterCreate, PersonalityTraits } from '@shared/types/character';
import styles from './CharacterCreatePage.module.css';

/* ---- Constants ---- */

const PRONOUN_OPTIONS = ['he/him', 'she/her', 'they/them', 'custom'] as const;

const BIG_FIVE: {
  key: keyof Omit<PersonalityTraits, 'custom'>;
  label: string;
  cnLabel: string;
  lowDesc: string;
  highDesc: string;
}[] = [
  {
    key: 'openness',
    label: 'Openness',
    cnLabel: '开放性',
    lowDesc: 'Conventional, practical',
    highDesc: 'Curious, creative',
  },
  {
    key: 'conscientiousness',
    label: 'Conscientiousness',
    cnLabel: '尽责性',
    lowDesc: 'Flexible, spontaneous',
    highDesc: 'Organized, disciplined',
  },
  {
    key: 'extraversion',
    label: 'Extraversion',
    cnLabel: '外向性',
    lowDesc: 'Reserved, solitary',
    highDesc: 'Outgoing, energetic',
  },
  {
    key: 'agreeableness',
    label: 'Agreeableness',
    cnLabel: '宜人性',
    lowDesc: 'Competitive, challenging',
    highDesc: 'Cooperative, trusting',
  },
  {
    key: 'neuroticism',
    label: 'Neuroticism',
    cnLabel: '神经质',
    lowDesc: 'Calm, confident',
    highDesc: 'Sensitive, emotional',
  },
];

const DEFAULT_SKILLS = ['Cooking', 'Charisma', 'Logic', 'Creativity', 'Athletics', 'Music'];

const HEIGHT_OPTIONS = ['short', 'average', 'tall'] as const;
const BUILD_OPTIONS = ['slim', 'average', 'athletic', 'heavy'] as const;

/* ---- Component ---- */

/**
 * Full character creation form with five sections:
 * Basic Info, Personality, Appearance, Background, and Skills.
 */
export default function CharacterCreatePage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { createCharacter, isLoading, error, clearError } = useCharacterStore();

  /* -- Basic Info state -- */
  const [name, setName] = useState('');
  const [species, setSpecies] = useState('human');
  const [age, setAge] = useState('');
  const [pronounsSelection, setPronounsSelection] = useState('they/them');
  const [customPronouns, setCustomPronouns] = useState('');
  const [description, setDescription] = useState('');

  /* -- Personality state -- */
  const [bigFive, setBigFive] = useState<Record<string, number>>({
    openness: 50,
    conscientiousness: 50,
    extraversion: 50,
    agreeableness: 50,
    neuroticism: 50,
  });
  const [customTraits, setCustomTraits] = useState<string[]>([]);
  const [customTraitInput, setCustomTraitInput] = useState('');

  /* -- Appearance state -- */
  const [hairColor, setHairColor] = useState('#4a3728');
  const [hairColorText, setHairColorText] = useState('Brown');
  const [eyeColor, setEyeColor] = useState('#5b7553');
  const [eyeColorText, setEyeColorText] = useState('Green');
  const [height, setHeight] = useState('average');
  const [build, setBuild] = useState('average');
  const [distinguishingFeatures, setDistinguishingFeatures] = useState('');

  /* -- Background state -- */
  const [backstory, setBackstory] = useState('');
  const [occupation, setOccupation] = useState('');
  const [likes, setLikes] = useState<string[]>([]);
  const [likeInput, setLikeInput] = useState('');
  const [dislikes, setDislikes] = useState<string[]>([]);
  const [dislikeInput, setDislikeInput] = useState('');

  /* -- Skills state -- */
  const [skills, setSkills] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    DEFAULT_SKILLS.forEach((s) => (initial[s] = 3));
    return initial;
  });
  const [customSkillInput, setCustomSkillInput] = useState('');

  /* -- Validation state -- */
  const [nameError, setNameError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  /* ---- Helpers ---- */

  const effectivePronouns =
    pronounsSelection === 'custom' ? customPronouns : pronounsSelection;

  const handleBigFiveChange = useCallback((key: string, value: number) => {
    setBigFive((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleSkillChange = useCallback((skillName: string, value: number) => {
    setSkills((prev) => ({ ...prev, [skillName]: value }));
  }, []);

  /* -- Tag helpers -- */
  const addTag = (
    value: string,
    list: string[],
    setList: React.Dispatch<React.SetStateAction<string[]>>,
    setInput: React.Dispatch<React.SetStateAction<string>>,
  ) => {
    const trimmed = value.trim();
    if (trimmed && !list.includes(trimmed)) {
      setList((prev) => [...prev, trimmed]);
    }
    setInput('');
  };

  const removeTag = (
    tag: string,
    setList: React.Dispatch<React.SetStateAction<string[]>>,
  ) => {
    setList((prev) => prev.filter((t) => t !== tag));
  };

  const handleTagKeyDown = (
    e: KeyboardEvent<HTMLInputElement>,
    value: string,
    list: string[],
    setList: React.Dispatch<React.SetStateAction<string[]>>,
    setInput: React.Dispatch<React.SetStateAction<string>>,
  ) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag(value, list, setList, setInput);
    }
  };

  /* -- Add custom skill -- */
  const addCustomSkill = () => {
    const trimmed = customSkillInput.trim();
    if (trimmed && !(trimmed in skills)) {
      setSkills((prev) => ({ ...prev, [trimmed]: 3 }));
      setCustomSkillInput('');
    }
  };

  const removeSkill = (skillName: string) => {
    setSkills((prev) => {
      const next = { ...prev };
      delete next[skillName];
      return next;
    });
  };

  /* ---- Form submission ---- */

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    clearError();

    // Validate
    if (!name.trim()) {
      setNameError('Character name is required.');
      return;
    }
    setNameError('');

    // Build appearance description
    const appearanceParts: string[] = [];
    if (hairColorText) appearanceParts.push(`Hair: ${hairColorText}`);
    if (eyeColorText) appearanceParts.push(`Eyes: ${eyeColorText}`);
    if (height !== 'average') appearanceParts.push(`Height: ${height}`);
    if (build !== 'average') appearanceParts.push(`Build: ${build}`);
    if (distinguishingFeatures.trim()) appearanceParts.push(distinguishingFeatures.trim());

    // Build full description
    const descParts: string[] = [];
    if (description.trim()) descParts.push(description.trim());
    if (appearanceParts.length > 0) {
      descParts.push(`[Appearance] ${appearanceParts.join('. ')}`);
    }

    // Build personality traits
    const personalityTraits: PersonalityTraits = {
      openness: bigFive.openness,
      conscientiousness: bigFive.conscientiousness,
      extraversion: bigFive.extraversion,
      agreeableness: bigFive.agreeableness,
      neuroticism: bigFive.neuroticism,
      custom: {},
    };
    customTraits.forEach((trait) => {
      personalityTraits.custom[trait] = 50;
    });

    // Build skills list
    const skillsList = Object.entries(skills).map(
      ([skillName, level]) => `${skillName}:${level}`,
    );

    // Build interests from likes
    const interests = [...likes];

    // Build backstory with occupation and dislikes appended
    const backstoryParts: string[] = [];
    if (backstory.trim()) backstoryParts.push(backstory.trim());
    if (occupation.trim()) backstoryParts.push(`Occupation: ${occupation.trim()}`);
    if (dislikes.length > 0) backstoryParts.push(`Dislikes: ${dislikes.join(', ')}`);

    const payload: CharacterCreate = {
      name: name.trim(),
      species: species.trim() || 'human',
      pronouns: effectivePronouns || 'they/them',
      age: age ? parseInt(age, 10) : null,
      description: descParts.join('\n'),
      backstory: backstoryParts.join('\n'),
      personalityTraits,
      interests,
      skills: skillsList,
      isPublic: false,
    };

    try {
      await createCharacter(payload);
      navigate('/dashboard');
    } catch {
      // Error is already set in the store
    }
  };

  /* ---- Auth guard ---- */

  if (!isAuthenticated) {
    return (
      <div className={styles.page}>
        <div className={styles.container}>
          <div className={styles.header}>
            <button className={styles.backBtn} onClick={() => navigate('/')}>
              &larr; Back to Home
            </button>
            <h1 className={styles.title}>Create Character</h1>
          </div>
          <div className={styles.authGuard}>
            <h3>Sign in required</h3>
            <p>You need to be logged in to create a character.</p>
            <button className={styles.authGuardBtn} onClick={() => navigate('/')}>
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  /* ---- Render ---- */

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        {/* Header */}
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={() => navigate('/dashboard')}>
            &larr; Back to Dashboard
          </button>
          <h1 className={styles.title}>Create Character</h1>
          <p className={styles.subtitle}>
            Bring a new original character to life. Fill in their details and
            personality, then drop them into a world.
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className={styles.errorBanner}>
            <span>{error}</span>
            <button className={styles.errorBannerClose} onClick={clearError}>
              &times;
            </button>
          </div>
        )}

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          {/* ======== Section 1: Basic Info ======== */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Basic Info</h2>
            <div className={styles.fieldGroup}>
              {/* Name */}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="cc-name">
                  Name<span className={styles.required}>*</span>
                </label>
                <input
                  id="cc-name"
                  type="text"
                  className={`${styles.input} ${submitted && nameError ? styles.inputError : ''}`}
                  placeholder="Your character's name"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (e.target.value.trim()) setNameError('');
                  }}
                />
                {submitted && nameError && (
                  <span className={styles.fieldError}>{nameError}</span>
                )}
              </div>

              <div className={styles.fieldRow}>
                {/* Species */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="cc-species">
                    Species
                  </label>
                  <input
                    id="cc-species"
                    type="text"
                    className={styles.input}
                    placeholder="human"
                    value={species}
                    onChange={(e) => setSpecies(e.target.value)}
                  />
                </div>

                {/* Age */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="cc-age">
                    Age
                  </label>
                  <input
                    id="cc-age"
                    type="number"
                    className={styles.input}
                    placeholder="Optional"
                    min={0}
                    max={9999}
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                  />
                </div>
              </div>

              {/* Pronouns */}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="cc-pronouns">
                  Pronouns
                </label>
                <div className={styles.fieldRow}>
                  <select
                    id="cc-pronouns"
                    className={styles.select}
                    value={pronounsSelection}
                    onChange={(e) => setPronounsSelection(e.target.value)}
                  >
                    {PRONOUN_OPTIONS.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt === 'custom' ? 'Custom...' : opt}
                      </option>
                    ))}
                  </select>
                  {pronounsSelection === 'custom' && (
                    <input
                      type="text"
                      className={styles.input}
                      placeholder="e.g. xe/xem"
                      value={customPronouns}
                      onChange={(e) => setCustomPronouns(e.target.value)}
                    />
                  )}
                </div>
              </div>

              {/* Description */}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="cc-desc">
                  Short Description
                </label>
                <textarea
                  id="cc-desc"
                  className={styles.textarea}
                  placeholder="A brief overview of your character..."
                  maxLength={500}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
                <span
                  className={`${styles.charCount} ${description.length > 450 ? styles.charCountWarn : ''}`}
                >
                  {description.length}/500
                </span>
              </div>
            </div>
          </div>

          {/* ======== Section 2: Personality ======== */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Personality (Big Five)</h2>
            <div className={styles.sliderGroup}>
              {BIG_FIVE.map((trait) => (
                <div key={trait.key} className={styles.sliderItem}>
                  <div className={styles.sliderHeader}>
                    <span className={styles.sliderLabel}>
                      {trait.label}
                      <span className={styles.sliderCnLabel}>({trait.cnLabel})</span>
                    </span>
                    <span className={styles.sliderValue}>{bigFive[trait.key]}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={bigFive[trait.key]}
                    className={styles.slider}
                    onChange={(e) =>
                      handleBigFiveChange(trait.key, parseInt(e.target.value, 10))
                    }
                  />
                  <div className={styles.sliderDesc}>
                    <span>{trait.lowDesc}</span>
                    <span>{trait.highDesc}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Custom traits */}
            <div className={styles.field} style={{ marginTop: '1.5rem' }}>
              <label className={styles.label}>Custom Traits</label>
              <div className={styles.tagInputWrapper}>
                <div className={styles.tagInputRow}>
                  <input
                    type="text"
                    className={styles.input}
                    placeholder="Type a trait and press Enter..."
                    value={customTraitInput}
                    onChange={(e) => setCustomTraitInput(e.target.value)}
                    onKeyDown={(e) =>
                      handleTagKeyDown(
                        e,
                        customTraitInput,
                        customTraits,
                        setCustomTraits,
                        setCustomTraitInput,
                      )
                    }
                  />
                  <button
                    type="button"
                    className={styles.addBtn}
                    onClick={() =>
                      addTag(
                        customTraitInput,
                        customTraits,
                        setCustomTraits,
                        setCustomTraitInput,
                      )
                    }
                  >
                    Add
                  </button>
                </div>
                {customTraits.length > 0 && (
                  <div className={styles.tags}>
                    {customTraits.map((trait) => (
                      <span key={trait} className={styles.tag}>
                        {trait}
                        <button
                          type="button"
                          className={styles.tagDelete}
                          onClick={() => removeTag(trait, setCustomTraits)}
                          aria-label={`Remove ${trait}`}
                        >
                          &times;
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ======== Section 3: Appearance ======== */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Appearance</h2>
            <div className={styles.fieldGroup}>
              <div className={styles.fieldRow}>
                {/* Hair color */}
                <div className={styles.field}>
                  <label className={styles.label}>Hair Color</label>
                  <div className={styles.colorFieldRow}>
                    <input
                      type="color"
                      className={styles.colorPicker}
                      value={hairColor}
                      onChange={(e) => setHairColor(e.target.value)}
                    />
                    <input
                      type="text"
                      className={`${styles.input} ${styles.colorTextInput}`}
                      placeholder="e.g. Brown"
                      value={hairColorText}
                      onChange={(e) => setHairColorText(e.target.value)}
                    />
                  </div>
                </div>

                {/* Eye color */}
                <div className={styles.field}>
                  <label className={styles.label}>Eye Color</label>
                  <div className={styles.colorFieldRow}>
                    <input
                      type="color"
                      className={styles.colorPicker}
                      value={eyeColor}
                      onChange={(e) => setEyeColor(e.target.value)}
                    />
                    <input
                      type="text"
                      className={`${styles.input} ${styles.colorTextInput}`}
                      placeholder="e.g. Green"
                      value={eyeColorText}
                      onChange={(e) => setEyeColorText(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className={styles.fieldRow}>
                {/* Height */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="cc-height">
                    Height
                  </label>
                  <select
                    id="cc-height"
                    className={styles.select}
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                  >
                    {HEIGHT_OPTIONS.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt.charAt(0).toUpperCase() + opt.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Build */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="cc-build">
                    Build
                  </label>
                  <select
                    id="cc-build"
                    className={styles.select}
                    value={build}
                    onChange={(e) => setBuild(e.target.value)}
                  >
                    {BUILD_OPTIONS.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt.charAt(0).toUpperCase() + opt.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Distinguishing features */}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="cc-features">
                  Distinguishing Features
                </label>
                <textarea
                  id="cc-features"
                  className={styles.textarea}
                  placeholder="Scars, tattoos, unusual markings, fashion style..."
                  value={distinguishingFeatures}
                  onChange={(e) => setDistinguishingFeatures(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* ======== Section 4: Background ======== */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Background</h2>
            <div className={styles.fieldGroup}>
              {/* Backstory */}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="cc-backstory">
                  Backstory
                </label>
                <textarea
                  id="cc-backstory"
                  className={`${styles.textarea} ${styles.textareaLarge}`}
                  placeholder="Where did they come from? What shaped them?"
                  value={backstory}
                  onChange={(e) => setBackstory(e.target.value)}
                />
              </div>

              {/* Occupation */}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="cc-occupation">
                  Occupation
                </label>
                <input
                  id="cc-occupation"
                  type="text"
                  className={styles.input}
                  placeholder="e.g. Blacksmith, Student, Freelancer..."
                  value={occupation}
                  onChange={(e) => setOccupation(e.target.value)}
                />
              </div>

              {/* Likes */}
              <div className={styles.field}>
                <label className={styles.label}>Likes</label>
                <div className={styles.tagInputWrapper}>
                  <div className={styles.tagInputRow}>
                    <input
                      type="text"
                      className={styles.input}
                      placeholder="Type something they like and press Enter..."
                      value={likeInput}
                      onChange={(e) => setLikeInput(e.target.value)}
                      onKeyDown={(e) =>
                        handleTagKeyDown(e, likeInput, likes, setLikes, setLikeInput)
                      }
                    />
                    <button
                      type="button"
                      className={styles.addBtn}
                      onClick={() =>
                        addTag(likeInput, likes, setLikes, setLikeInput)
                      }
                    >
                      Add
                    </button>
                  </div>
                  {likes.length > 0 && (
                    <div className={styles.tags}>
                      {likes.map((tag) => (
                        <span key={tag} className={styles.tag}>
                          {tag}
                          <button
                            type="button"
                            className={styles.tagDelete}
                            onClick={() => removeTag(tag, setLikes)}
                            aria-label={`Remove ${tag}`}
                          >
                            &times;
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Dislikes */}
              <div className={styles.field}>
                <label className={styles.label}>Dislikes</label>
                <div className={styles.tagInputWrapper}>
                  <div className={styles.tagInputRow}>
                    <input
                      type="text"
                      className={styles.input}
                      placeholder="Type something they dislike and press Enter..."
                      value={dislikeInput}
                      onChange={(e) => setDislikeInput(e.target.value)}
                      onKeyDown={(e) =>
                        handleTagKeyDown(
                          e,
                          dislikeInput,
                          dislikes,
                          setDislikes,
                          setDislikeInput,
                        )
                      }
                    />
                    <button
                      type="button"
                      className={styles.addBtn}
                      onClick={() =>
                        addTag(dislikeInput, dislikes, setDislikes, setDislikeInput)
                      }
                    >
                      Add
                    </button>
                  </div>
                  {dislikes.length > 0 && (
                    <div className={styles.tags}>
                      {dislikes.map((tag) => (
                        <span key={tag} className={styles.tag}>
                          {tag}
                          <button
                            type="button"
                            className={styles.tagDelete}
                            onClick={() => removeTag(tag, setDislikes)}
                            aria-label={`Remove ${tag}`}
                          >
                            &times;
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* ======== Section 5: Skills ======== */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>Skills</h2>
            <div className={styles.sliderGroup}>
              {Object.entries(skills).map(([skillName, level]) => (
                <div key={skillName} className={styles.sliderItem}>
                  <div className={styles.sliderHeader}>
                    <span className={styles.sliderLabel}>
                      {skillName}
                      {!DEFAULT_SKILLS.includes(skillName) && (
                        <button
                          type="button"
                          className={styles.removeSkillBtn}
                          onClick={() => removeSkill(skillName)}
                          aria-label={`Remove ${skillName} skill`}
                        >
                          (remove)
                        </button>
                      )}
                    </span>
                    <span className={styles.skillValue}>{level}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={10}
                    value={level}
                    className={styles.skillSlider}
                    onChange={(e) =>
                      handleSkillChange(skillName, parseInt(e.target.value, 10))
                    }
                  />
                  <div className={styles.sliderDesc}>
                    <span>Novice</span>
                    <span>Master</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Add custom skill */}
            <div className={styles.addSkillRow}>
              <input
                type="text"
                className={styles.input}
                placeholder="Add a custom skill..."
                value={customSkillInput}
                onChange={(e) => setCustomSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addCustomSkill();
                  }
                }}
              />
              <button
                type="button"
                className={styles.addBtn}
                onClick={addCustomSkill}
              >
                Add Skill
              </button>
            </div>
          </div>

          {/* ======== Submit ======== */}
          <div className={styles.submitArea}>
            <button
              type="button"
              className={styles.cancelBtn}
              onClick={() => navigate('/dashboard')}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className={styles.spinner} />
                  Creating...
                </>
              ) : (
                'Create Character'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

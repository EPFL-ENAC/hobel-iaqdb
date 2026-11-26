export type GlossaryCategory =
  'climate' | 'ventilation' | 'pollutants' | 'statistics' | 'metadata';

export interface GlossaryEntry {
  key: string;
  term: string;
  category: GlossaryCategory;
  definition: string;
  aliases?: string[];
}

export interface KoppenClimate {
  code: string;
  name: string;
  detail: string;
}

/**
 * Full Köppen-Geiger climate names shown next to codes ("Cfb, temperate oceanic")
 * and their 3-letter scheme breakdown for tooltips and the glossary.
 */
export const KOPPEN_CLIMATES: readonly KoppenClimate[] = [
  {
    code: 'Af',
    name: 'tropical rainforest',
    detail: 'Tropical, rainforest (no dry season).',
  },
  { code: 'Am', name: 'tropical monsoon', detail: 'Tropical, monsoon.' },
  {
    code: 'Aw',
    name: 'tropical savanna',
    detail: 'Tropical, dry winter savanna.',
  },
  { code: 'BWh', name: 'hot desert', detail: 'Arid, hot desert.' },
  { code: 'BWk', name: 'cold desert', detail: 'Arid, cold desert.' },
  { code: 'BSh', name: 'hot semi-arid', detail: 'Arid, hot steppe.' },
  { code: 'BSk', name: 'cold semi-arid', detail: 'Arid, cold steppe.' },
  {
    code: 'Csa',
    name: 'hot-summer Mediterranean',
    detail: 'Temperate, dry hot summer.',
  },
  {
    code: 'Csb',
    name: 'warm-summer Mediterranean',
    detail: 'Temperate, dry warm summer.',
  },
  {
    code: 'Csc',
    name: 'cold-summer Mediterranean',
    detail: 'Temperate, dry cold summer.',
  },
  {
    code: 'Cwa',
    name: 'monsoon-influenced humid subtropical',
    detail: 'Temperate, dry winter, hot summer.',
  },
  {
    code: 'Cwb',
    name: 'subtropical highland',
    detail: 'Temperate, dry winter, warm summer.',
  },
  {
    code: 'Cwc',
    name: 'cold subtropical highland',
    detail: 'Temperate, dry winter, cold summer.',
  },
  {
    code: 'Cfa',
    name: 'humid subtropical',
    detail: 'Temperate, no dry season, hot summer.',
  },
  {
    code: 'Cfb',
    name: 'temperate oceanic',
    detail: 'Temperate, no dry season, warm summer.',
  },
  {
    code: 'Cfc',
    name: 'subpolar oceanic',
    detail: 'Temperate, no dry season, cold summer.',
  },
  {
    code: 'Dsa',
    name: 'hot-summer continental (dry summer)',
    detail: 'Continental, dry hot summer.',
  },
  {
    code: 'Dsb',
    name: 'warm-summer continental (dry summer)',
    detail: 'Continental, dry warm summer.',
  },
  {
    code: 'Dsc',
    name: 'subarctic (dry summer)',
    detail: 'Continental, dry cold summer.',
  },
  {
    code: 'Dsd',
    name: 'extremely cold subarctic (dry summer)',
    detail: 'Continental, dry summer, very cold winter.',
  },
  {
    code: 'Dwa',
    name: 'monsoon-influenced hot-summer continental',
    detail: 'Continental, dry winter, hot summer.',
  },
  {
    code: 'Dwb',
    name: 'monsoon-influenced warm-summer continental',
    detail: 'Continental, dry winter, warm summer.',
  },
  {
    code: 'Dwc',
    name: 'monsoon-influenced subarctic',
    detail: 'Continental, dry winter, cold summer.',
  },
  {
    code: 'Dwd',
    name: 'monsoon-influenced extremely cold subarctic',
    detail: 'Continental, dry winter, very cold winter.',
  },
  {
    code: 'Dfa',
    name: 'hot-summer humid continental',
    detail: 'Continental, no dry season, hot summer.',
  },
  {
    code: 'Dfb',
    name: 'warm-summer humid continental',
    detail: 'Continental, no dry season, warm summer.',
  },
  {
    code: 'Dfc',
    name: 'subarctic',
    detail: 'Continental, no dry season, cold summer.',
  },
  {
    code: 'Dfd',
    name: 'extremely cold subarctic',
    detail: 'Continental, no dry season, very cold winter.',
  },
  { code: 'ET', name: 'tundra', detail: 'Polar, tundra.' },
  { code: 'EF', name: 'ice cap', detail: 'Polar, frost / ice cap.' },
];

export const KOPPEN_GROUPS: readonly KoppenClimate[] = [
  {
    code: 'A',
    name: 'tropical',
    detail: 'Main Köppen group A: tropical climates.',
  },
  {
    code: 'B',
    name: 'arid',
    detail: 'Main Köppen group B: dry (arid and semi-arid) climates.',
  },
  {
    code: 'C',
    name: 'temperate',
    detail: 'Main Köppen group C: temperate climates.',
  },
  {
    code: 'D',
    name: 'continental',
    detail: 'Main Köppen group D: continental (cold) climates.',
  },
  { code: 'E', name: 'polar', detail: 'Main Köppen group E: polar climates.' },
];

const KOPPEN_MAP = new Map<string, KoppenClimate>(
  [...KOPPEN_CLIMATES, ...KOPPEN_GROUPS].map((c) => [c.code.toLowerCase(), c]),
);

/** "Cfb" -> "Cfb, temperate oceanic"; returns the input unchanged when unknown. */
export function formatClimateZone(code: string | null | undefined): string {
  if (!code) return '';
  const match = KOPPEN_MAP.get(code.trim().toLowerCase());
  return match ? `${match.code}, ${match.name}` : code;
}

const CORE_ENTRIES: readonly GlossaryEntry[] = [
  // Climate overview
  {
    key: 'koppen_climate',
    term: 'Köppen–Geiger climate codes',
    category: 'climate',
    definition:
      'Climate classification using 1 to 3 letters: first letter is the main group (A tropical, B arid, C temperate, D continental, E polar), second is seasonal precipitation, third is temperature.',
    aliases: ['climate zone', 'climate zones', 'climate_zone'],
  },

  // Ventilation
  {
    key: 'c-cfis',
    term: 'c-cfis',
    category: 'ventilation',
    definition:
      'Central fan integrated supply: outdoor air is drawn into the return duct and distributed through the building by the central HVAC air-handler fan.',
    aliases: ['cfis'],
  },
  {
    key: 'exh',
    term: 'exh',
    category: 'ventilation',
    definition:
      'Exhaust-only mechanical ventilation: fans extract stale indoor air while replacement outdoor air enters passively through vents or envelope leaks.',
    aliases: ['exhaust', 'exhaust only'],
  },
  {
    key: 'erv',
    term: 'erv',
    category: 'ventilation',
    definition:
      'Energy recovery ventilator: balanced mechanical ventilation system that exchanges both heat and moisture between outgoing stale air and incoming outdoor air.',
  },
  {
    key: 'exh + c-cfis',
    term: 'exh + c-cfis',
    category: 'ventilation',
    definition:
      'Combined mechanical exhaust ventilation (exh) and central fan integrated supply (c-cfis) operating in the same building or space.',
  },
  {
    key: 'mixing',
    term: 'Mixing ventilation',
    category: 'ventilation',
    definition:
      'Supply air is delivered at high velocity to mix thoroughly with room air and dilute indoor pollutants uniformly.',
    aliases: ['mixing'],
  },
  {
    key: 'displacement',
    term: 'Displacement ventilation',
    category: 'ventilation',
    definition:
      'Cool supply air is introduced slowly near floor level and rises as it warms, displacing warmer, more polluted air upward toward ceiling exhausts.',
    aliases: ['displacement'],
  },
  {
    key: 'balanced mechanical ventilation',
    term: 'Balanced mechanical ventilation',
    category: 'ventilation',
    definition:
      'Mechanical fans supply outdoor air and exhaust indoor air at roughly equal rates, often combined with heat or energy recovery.',
    aliases: ['balanced mechanical'],
  },
  {
    key: 'supply',
    term: 'Supply-only ventilation',
    category: 'ventilation',
    definition:
      'Mechanical fans deliver filtered outdoor air into indoor spaces while indoor air exits passively through vents or envelope leaks.',
    aliases: ['supply'],
  },
  {
    key: 'hybrid/mixed mode',
    term: 'Hybrid / mixed-mode ventilation',
    category: 'ventilation',
    definition:
      'Combines natural ventilation (operable windows or vents) with mechanical ventilation depending on outdoor conditions or occupancy.',
  },

  // Ventilation umbrella concepts
  {
    key: 'natural ventilation',
    term: 'Natural ventilation',
    category: 'ventilation',
    definition:
      'Air exchange driven passively by wind pressure and indoor–outdoor temperature differences through windows, doors, or openings.',
  },
  {
    key: 'mechanical ventilation',
    term: 'Mechanical ventilation',
    category: 'ventilation',
    definition:
      'Air exchange driven by powered fans or air-handling units to supply outdoor air, exhaust stale air, or both.',
  },

  // Pollutants & indices (from parameters.csv)
  {
    key: 'voc_index',
    term: 'VOC index',
    category: 'pollutants',
    definition:
      'Relative, dimensionless sensor index (commonly 1–500, baseline 100) indicating whether volatile organic compound levels are higher or lower than recent background air; not a mass concentration.',
    aliases: ['voc index'],
  },
  {
    key: 'iaqi',
    term: 'IAQ index',
    category: 'pollutants',
    definition:
      'Indoor air quality index: a composite, dimensionless score produced by a sensor algorithm (often 0–500, lower is cleaner) summarizing overall indoor air quality.',
    aliases: ['iaq index', 'indoor air quality index'],
  },
  {
    key: 'eiaqi',
    term: 'Extended IAQ index',
    category: 'pollutants',
    definition:
      'Extended indoor air quality index: an extended-range composite IAQ score that continues resolving heavily polluted conditions beyond the standard upper cap.',
    aliases: ['extended iaq index', 'extended indoor air quality index'],
  },
  {
    key: 'aqi',
    term: 'Air quality index',
    category: 'pollutants',
    definition:
      'Composite dimensionless score translating one or more pollutant concentrations into a single air quality scale for comparison across time or spaces.',
    aliases: ['air quality index', 'air_quality_score', 'air quality score'],
  },
  {
    key: 'particle_mass_concentration',
    term: 'Particle mass concentration',
    category: 'pollutants',
    definition:
      'Total mass of airborne suspended particulate matter per unit volume of air (typically in µg/m³), as opposed to particle count (number concentration).',
    aliases: [
      'particle mass concentration',
      'particle_mass_concentration_alveolar',
      'particle_mass_concentration_tracheobronchial',
      'particle_mass_concentration_head_airways',
    ],
  },
  {
    key: 'particle_number_concentration',
    term: 'Particle number concentration',
    category: 'pollutants',
    definition:
      'Count of airborne particles per unit volume of air (typically in #/cm³), sensitive to ultrafine particles that carry little mass.',
    aliases: [
      'particle number concentration',
      'particle_number',
      'pn1',
      'pn25',
      'pn10',
    ],
  },
  {
    key: 'total_ufp',
    term: 'Ultrafine particles (UFP)',
    category: 'pollutants',
    definition:
      'Airborne particles smaller than 0.1 µm (100 nm) in diameter, measured by number concentration (#/cm³).',
    aliases: ['ultrafine particle number concentration', 'ufp'],
  },
  {
    key: 'tvoc',
    term: 'TVOC',
    category: 'pollutants',
    definition:
      'Total volatile organic compounds: aggregate concentration of airborne organic chemicals that evaporate easily at room temperature (typically in ppb or µg/m³).',
    aliases: ['total volatile organic compounds', 'voc'],
  },
  {
    key: 'pm2_5',
    term: 'PM2.5',
    category: 'pollutants',
    definition:
      'Fine particulate matter with aerodynamic diameter ≤ 2.5 µm, small enough to reach deep into the lungs (measured in µg/m³).',
    aliases: ['pm2.5'],
  },
  {
    key: 'pm10',
    term: 'PM10',
    category: 'pollutants',
    definition:
      'Inhalable particulate matter with aerodynamic diameter ≤ 10 µm, including dust, pollen, and fine particles (measured in µg/m³).',
  },
  {
    key: 'pm1',
    term: 'PM1',
    category: 'pollutants',
    definition:
      'Sub-micron particulate matter with aerodynamic diameter ≤ 1 µm (measured in µg/m³).',
  },
  {
    key: 'ldsa',
    term: 'Lung deposited surface area (LDSA)',
    category: 'pollutants',
    definition:
      'Estimated surface area of airborne particles per unit volume (µm²/cm³) that deposits in the alveolar or tracheobronchial regions of the lungs.',
    aliases: [
      'lung deposited surface area',
      'particle_lung_deposited_surface_area_p',
    ],
  },
  {
    key: 'nox_index',
    term: 'NOx index',
    category: 'pollutants',
    definition:
      'Relative sensor index (typically 1–500, baseline 1) indicating changes in oxidizing gases such as nitrogen oxides compared to recent background air.',
    aliases: ['noxindex', 'nox index'],
  },
  {
    key: 'tci',
    term: 'Thermal comfort index',
    category: 'pollutants',
    definition:
      'Composite dimensionless indicator summarizing occupant thermal comfort from indoor environmental readings.',
    aliases: ['thermal comfort index'],
  },
  {
    key: 'avti',
    term: 'Ventilation index',
    category: 'pollutants',
    definition:
      'Composite dimensionless indicator summarizing ventilation adequacy in a measured space.',
    aliases: ['ventilation index'],
  },

  // Charts & statistics
  {
    key: 'middle_half',
    term: 'Middle half',
    category: 'statistics',
    definition:
      'Interquartile range (IQR): the span between the 25th and 75th percentiles containing the central 50% of values (drawn as the box in box plots and the shaded band in trend charts).',
    aliases: ['middle half', 'iqr', 'interquartile range'],
  },

  // Metadata & references
  {
    key: 'parameter_reference',
    term: 'Parameter reference',
    category: 'metadata',
    definition:
      'A guideline, standard, or legal threshold from an authoritative body (such as WHO, EPA, ANSES, or national regulations) used as a benchmark for a pollutant over a defined averaging period.',
    aliases: ['parameter reference', 'reference', 'benchmark'],
  },
  {
    key: 'older_adults',
    term: 'Older adults',
    category: 'metadata',
    definition:
      'Occupant age-group label used in studies for older adult or senior building occupants.',
    aliases: ['older adults', 'other adults'],
  },
  {
    key: 'airtightness',
    term: 'Airtightness (ACH50)',
    category: 'metadata',
    definition:
      'Air changes per hour measured at a 50 Pa pressure difference during a blower-door test; lower values mean a tighter building envelope.',
    aliases: ['ach50', 'airtightness (ach50)', 'building.airtightness'],
  },
  {
    key: 'air_change_rate',
    term: 'Air change rate',
    category: 'metadata',
    definition:
      'Number of times the entire volume of indoor air in a space is replaced by outdoor air per hour (h⁻¹).',
    aliases: ['air change rate', 'air_exchange_rate', 'air exchange rate'],
  },
  {
    key: 'data_embargo',
    term: 'Data embargo',
    category: 'metadata',
    definition:
      'Temporary restriction period set by study contributors during which raw measurements are visible in aggregate charts but excluded from downloads.',
    aliases: ['embargo', 'data embargo'],
  },
];

const CLIMATE_ENTRIES: readonly GlossaryEntry[] = [
  ...KOPPEN_GROUPS,
  ...KOPPEN_CLIMATES,
].map((c) => ({
  key: c.code,
  term: `${c.code}, ${c.name}`,
  category: 'climate' as const,
  definition: `Köppen–Geiger class ${c.code}: ${c.detail}`,
  aliases: [c.code.toLowerCase(), `${c.code}, ${c.name}`.toLowerCase()],
}));

/** Single list powering both inline tooltips and the Help Drawer glossary section. */
export const GLOSSARY: readonly GlossaryEntry[] = [
  ...CORE_ENTRIES,
  ...CLIMATE_ENTRIES,
];

export const GLOSSARY_CATEGORIES: readonly GlossaryCategory[] = [
  'pollutants',
  'ventilation',
  'climate',
  'statistics',
  'metadata',
];

const LOOKUP = new Map<string, GlossaryEntry>();
for (const entry of GLOSSARY) {
  LOOKUP.set(entry.key.toLowerCase(), entry);
  LOOKUP.set(entry.term.toLowerCase(), entry);
  for (const alias of entry.aliases ?? []) {
    LOOKUP.set(alias.toLowerCase(), entry);
  }
}

/** Find a glossary entry by slug, raw data key, or visible label (case-insensitive). */
export function lookupGlossary(
  ...candidates: (string | null | undefined)[]
): GlossaryEntry | undefined {
  for (const raw of candidates) {
    if (!raw) continue;
    const normalized = raw.trim().toLowerCase();
    const direct = LOOKUP.get(normalized);
    if (direct) return direct;
  }
  return undefined;
}

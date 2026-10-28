/**
 * The filters said in words: the values a section holds ("Netherlands",
 * "School", "2010–2024"), for the filter bar's pills and the dialog's list.
 */
import { keyLabel, shortParameterName } from '@/components/plots/charts';
import { SECTION_FIELDS, defaultDraft, type FilterDraft, type FilterSection } from '@/composables/useFilterDraft';
import { cityName } from '@/stores/filters';

export function useFilterSummary() {
  const { t } = useI18n();

  function range(value: { min: number; max: number }, unit = ''): string {
    return `${value.min}${unit}–${value.max}${unit}`;
  }

  /** the values a section holds, in words; none when it is at its defaults */
  function values(draft: FilterDraft, section: FilterSection): string[] {
    const defaults = defaultDraft();
    const out: string[] = [];
    const ranged = (field: 'measurement_years' | 'altitudes' | 'construction_years', unit = '') => {
      const value = draft[field];
      const fallback = defaults[field];
      if (value.min !== fallback.min || value.max !== fallback.max) out.push(range(value, unit));
    };
    for (const field of SECTION_FIELDS[section]) {
      switch (field) {
        case 'parameters':
          out.push(...draft.parameters.map(shortParameterName));
          break;
        case 'measurement_years':
        case 'construction_years':
          ranged(field);
          break;
        case 'altitudes':
          ranged(field, ' m');
          break;
        case 'countries':
          out.push(...draft.countries.map((key) => keyLabel('country', key)));
          break;
        case 'cities':
          out.push(...draft.cities.map(cityName));
          break;
        case 'climate_zones':
          out.push(...draft.climate_zones);
          break;
        case 'building_types':
          out.push(...draft.building_types.map((key) => keyLabel('building_type', key)));
          break;
        case 'study_ids':
          out.push(...draft.study_ids.map((key) => keyLabel('study', key)));
          break;
        case 'mechanical_ventilation':
          if (draft.mechanical_ventilation)
            out.push(t('filter_bar.ventilation_value', { value: keyLabel('ventilation', draft.mechanical_ventilation) }));
          break;
        case 'mechanical_ventilation_types':
          out.push(...draft.mechanical_ventilation_types.map((key) => keyLabel('ventilation_type', key)));
          break;
        case 'outdoor_envs':
          out.push(...draft.outdoor_envs.map((key) => keyLabel('outdoor_env', key)));
          break;
        case 'age_groups':
          out.push(...draft.age_groups.map((key) => keyLabel('age_group', key)));
          break;
        case 'socioeconomic_status':
          out.push(...draft.socioeconomic_status.map((key) => keyLabel('socioeconomic_status', key)));
          break;
      }
    }
    return out;
  }

  /** "Netherlands", "Netherlands +2", or the section's "any …" */
  function pill(draft: FilterDraft, section: FilterSection): string {
    const items = values(draft, section);
    if (!items.length) return t(`filter_bar.any.${section}`);
    return items.length === 1 ? (items[0] ?? '') : `${items[0]} +${items.length - 1}`;
  }

  /** the pollutants alone, for the bar's first pill */
  function pollutants(draft: FilterDraft): string {
    if (!draft.parameters.length) return t('filter_bar.any_pollutant');
    const names = draft.parameters.map(shortParameterName);
    return names.length <= 2 ? names.join(', ') : `${names[0]} +${names.length - 1}`;
  }

  /** the measurement years alone, for the bar's second pill */
  function years(draft: FilterDraft): string {
    const fallback = defaultDraft().measurement_years;
    const value = draft.measurement_years;
    return value.min === fallback.min && value.max === fallback.max ? t('filter_bar.any_year') : range(value);
  }

  return { values, pill, pollutants, years };
}


import { defineBoot } from '#q-app'
import { useSettingsStore } from '@/stores/settings';

export default defineBoot(() => {
  const settingsStore = useSettingsStore();
  settingsStore.initSettings();
});

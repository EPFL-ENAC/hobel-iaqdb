<template>
  <div>
    <q-list>
      <q-item-label header class="q-pt-none">
        <span class="text-h6">
          <q-icon name="domain" class="q-pb-xs" />
          <span class="q-ml-sm">{{ t('plots.buildings_overview') }}</span>
        </span>
      </q-item-label>
    </q-list>
    <div class="text-caption text-bold q-ml-md">{{ t('plots.building_type') }}</div>
    <MetadataTreemapChart entity="buildings" by="building_type" :options="buildingTypeOptions" :colors="['#00441b', '#b7e2b1']" />
    <div class="text-caption text-bold q-ml-md q-mt-sm">{{ t('plots.building_country') }}</div>
    <MetadataTreemapChart entity="buildings" by="country" :options="countryOptions" :colors="['#08306b', '#93c3df']" />
    <div class="text-caption text-bold q-ml-md q-mt-sm">{{ t('plots.building_ventilation') }}</div>
    <MetadataTreemapChart entity="buildings" by="ventilation" :options="yesNoOptions" :colors="['#3f007d', '#bcbddc']" />
    <q-list>
      <q-item-label header>
        <span class="text-h6">
          <q-icon name="living" class="q-pb-xs" />
          <span class="q-ml-sm">{{ t('plots.spaces_overview') }}</span>
        </span>
      </q-item-label>
    </q-list>
    <div class="text-caption text-bold q-ml-md q-mt-sm">{{ t('plots.space_type') }}</div>
    <MetadataTreemapChart entity="spaces" by="space_type" :options="spaceTypeOptions" :colors="['#800026', '#ffefa5']" />
    <div class="text-caption text-bold q-ml-md q-mt-sm">{{ t('plots.space_ventilation_type') }}</div>
    <MetadataTreemapChart entity="spaces" by="ventilation_type" :options="mechanicalVentilationTypeOptions" :colors="['#7f2704', '#fdd0a2']" />
  </div>
</template>

<script setup lang="ts">
import MetadataTreemapChart from '@/components/plots/MetadataTreemapChart.vue';
import {
  buildingTypeOptions,
  countryOptions,
  mechanicalVentilationTypeOptions,
  spaceTypeOptions,
  yesNoOptions,
} from '@/utils/options';

const { t } = useI18n();
</script>

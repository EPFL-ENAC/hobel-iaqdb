<template>
  <div>
    <q-input
      v-model="building.identifier"
      filled
      :label="t('study.building.identifier') + ' *'"
      :hint="t('study.building.identifier_hint')"
      :rules="[val => !!val || t('required')]"
      class="q-mb-md"
    />

    <div class="row q-col-gutter-md q-mb-md q-mt-md">
      <div class="col">
        <q-select
          v-model="building.type"
          :options="buildingTypeOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.type') + ' *'"
          :hint="t('study.building.type_hint')"
          :rules="[val => !!val || t('required')]"
          @update:model-value="onBuildingTypeChange"
        />
      </div>
      <div v-if="building.type === 'other'" class="col">
        <q-input
          v-model="building.other_type"
          filled
          :label="t('study.building.other_type')"
          :hint="t('study.building.other_type_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.outdoor_env"
          :options="outdoorEnvOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.outdoor_env')"
          :hint="t('study.building.outdoor_env_hint')"
          @update:model-value="onOutdoorEnvChange"
        />
      </div>
      <div v-if="building.outdoor_env === 'other'" class="col">
        <q-input
          v-model="building.other_outdoor_env"
          filled
          :label="t('study.building.other_outdoor_env')"
          :hint="t('study.building.other_outdoor_env_hint')"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-sm">
      <div class="col">
        <q-input
          v-model.number="building.construction_year"
          filled
          type="number"
          :min="0"
          :max="new Date().getFullYear()"
          :label="t('study.building.construction_year')"
          :hint="t('study.building.construction_year_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.renovation"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.renovation')"
          :hint="t('study.building.renovation_hint')"
          @update:model-value="onRenovationUpdated"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="building.renovation_year"
          filled
          type="number"
          :min="0"
          :max="new Date().getFullYear()"
          :label="t('study.building.renovation_year')"
          :hint="t('study.building.renovation_year_hint')"
          :disable="building.renovation !== 'yes'"
        />
      </div>
      <div class="col">
        <q-input
          v-model="building.renovation_details"
          filled
          type="textarea"
          :label="t('study.building.renovation_details')"
          :hint="t('study.building.renovation_details_hint')"
          :disable="building.renovation !== 'yes'"
        />
      </div>
    </div>
    
    <div class="text-bold q-mb-md">Location</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model="building.city"
          filled
          :label="t('study.building.city') + ' *'"
          :hint="t('study.building.city_hint')"
          :rules="[val => !!val || t('required')]"
          :debounce="1000"
          @update:model-value="onLocationUpdated"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.country"
          :options="countryOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.country') + ' *'"
          :hint="t('study.building.country_hint')"
          :rules="[val => !!val || t('required')]"
          @update:model-value="onLocationUpdated"
        />
      </div>
    </div>

    <div v-if="authStore.isAdmin && hasCityCountry" class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="building.long"
          type="number"
          :min="-180"
          :max="180"
          filled
          :label="t('study.building.longitude')"
          :hint="t('study.building.longitude_hint')"
          :disable="loadingGeo"
          :loading="loadingGeo"
          @update:model-value="onLongLatUpdated"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="building.lat"
          type="number"
          :min="-90"
          :max="90"
          filled
          :label="t('study.building.latitude')"
          :hint="t('study.building.latitude_hint')"
          :disable="loadingGeo"
          :loading="loadingGeo"
          @update:model-value="onLongLatUpdated"
        />
      </div>
    </div>
    <div v-if="authStore.isAdmin && hasLongLat" class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="building.altitude"
          type="number"
          :min="-1000"
          :max="10000"
          filled
          :label="t('study.building.altitude')"
          :hint="t('study.building.altitude_hint')"
          :disable="loadingGeo || loadingAlt"
          :loading="loadingGeo || loadingAlt"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.climate_zone"
          :options="climateOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.climate_zone')"
          :hint="t('study.building.climate_zone_hint')"
          :disable="loadingGeo || loadingAlt"
          :loading="loadingGeo || loadingAlt"
        />
      </div>
    </div>
    <div v-if="authStore.isAdmin && loadingAlt">
      <q-spinner-dots />
    </div>

    <div class="text-bold q-mb-md">Ventilation</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="building.mechanical_ventilation"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.mechanical_ventilation')"
          :hint="t('study.building.mechanical_ventilation_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model="building.particle_filtration_system"
          filled
          :label="t('study.building.particle_filtration_system')"
          :hint="t('study.building.particle_filtration_system_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="building.particle_filtration_rating"
          type="number"
          :min="0"
          filled
          :label="t('study.building.particle_filtration_rating')"
          :hint="t('study.building.particle_filtration_rating_hint')"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="building.operable_windows"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.operable_windows')"
          :hint="t('study.building.operable_windows_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="building.airtightness"
          type="number"
          :min="0"
          filled
          :label="t('study.building.airtightness')"
          :hint="t('study.building.airtightness_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.smoking"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.smoking')"
          :hint="t('study.building.smoking_hint')"
        />
      </div>
    </div>

    <div class="text-bold q-mb-md">Occupancy</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="building.age_group"
          :options="ageGroupOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.age_group')"
          :hint="t('study.building.age_group_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.socioeconomic_status"
          :options="socioeconomicStatusOptions"
          filled
          emit-value
          map-options
          :label="t('study.building.socioeconomic_status')"
          :hint="t('study.building.socioeconomic_status_hint')"
        />
      </div>
    </div>

    <div class="text-bold q-mb-md">Certification</div>
    <div class="q-mb-md">
      <q-select
        v-model="building.green_certified"
        :options="yesNoOptions"
        filled
        emit-value
        map-options
        :label="t('study.building.green_certified')"
        :hint="t('study.building.green_certified_hint')"
        @update:model-value="onGreenCertifiedUpdated"
      />
    </div>

    <div
      v-if="building.certifications?.length"
      class="row q-col-gutter-md q-mb-md"
    >
      <div class="col">
        <q-input
          v-if="building.certifications[0]"
          v-model.number="building.certifications[0].program"
          filled
          :label="t('study.building.certification_program')"
          :hint="t('study.building.certification_program_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-if="building.certifications[0]"
          v-model.number="building.certifications[0].level"
          filled
          :label="t('study.building.certification_level')"
          :hint="t('study.building.certification_level_hint')"
        />
      </div>
    </div>

    <div class="text-bold q-mb-md">Spaces</div>
    <q-card flat bordered class="q-mb-md bg-grey-2">
      <q-card-section>
        <div v-if="building.spaces?.length === 0" class="text-help">
          No spaces defined yet.
        </div>
        <q-list separator>
          <template v-for="(space, i) in building.spaces" :key="space.id">
            <q-item class="q-pl-none q-pr-none">
              <q-item-section>
                <q-expansion-item
                  dense
                  label="..."
                  header-class="text-bold text-secondary"
                >
                  <template v-slot:header>
                    {{
                      `${building.spaces ? building.spaces[i]?.identifier : i}`
                    }}
                  </template>
                  <space-form
                    v-if="building.spaces && building.spaces[i]"
                    v-model="building.spaces[i]"
                    :building="building"
                    class="q-mt-md"
                  />
                </q-expansion-item>
              </q-item-section>
              <q-item-section side>
                <div>
                  <q-btn
                    rounded
                    dense
                    flat
                    :title="t('duplicate')"
                    icon="content_copy"
                    size="sm"
                    @click="onDuplicateSpace(i)"
                  />
                  <q-btn
                    rounded
                    dense
                    flat
                    color="negative"
                    :title="t('delete')"
                    icon="delete"
                    size="sm"
                    @click="onDeleteSpace(i)"
                  />
                </div>
              </q-item-section>
            </q-item>
          </template>
        </q-list>
      </q-card-section>
      <q-card-actions class="bg-grey-3 q-pa-md">
        <q-btn
          @click="onAddSpace"
          color="secondary"
          label="Add Space"
          icon="add"
          size="sm"
        />
      </q-card-actions>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import {
  climateOptions,
  buildingTypeOptions,
  outdoorEnvOptions,
  ageGroupOptions,
  socioeconomicStatusOptions,
  countryOptions,
  yesNoOptions,
} from 'src/utils/options';
import { geocoderApi } from 'src/utils/geocoder';
import type { Building, Certification } from 'src/models';
import SpaceForm from 'src/components/contribute/SpaceForm.vue';
import { notifyInfo } from 'src/utils/notify';

const { t } = useI18n();
const contrib = useContributeStore();
const authStore = useAuthStore();

interface Props {
  modelValue: Building;
}
const props = defineProps<Props>();

const building = ref<Building>(props.modelValue);
const loadingGeo = ref(false);
const loadingAlt = ref(false);

onMounted(() => {
  void onInitLocation();
  onGreenCertifiedUpdated();
});

watch(() => props.modelValue, (val) => {
  building.value = val;
  void onInitLocation();
  onGreenCertifiedUpdated();
});

const hasCityCountry = computed(
  () => building.value.city && building.value.country,
);
const hasLongLat = computed(
  () => building.value.long && building.value.lat,
);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function isNumber(value: any): boolean {
  return typeof value === 'number' && !isNaN(value);
}

async function onInitLocation() {
  building.value.postcode = undefined; // Reset postcode as it is not used anymore
  if (!hasCityCountry.value) {
    building.value.long = undefined;
    building.value.lat = undefined;
    onLongLatUpdated();
    return;
  } else {
    // check if country is an option label instead of value
    const countryOpt = countryOptions.find((c) => c.label === building.value.country);
    if (countryOpt) {
      building.value.country = countryOpt.value;
      await onLocationUpdated();
    } else if (!isNumber(building.value.long) || !isNumber(building.value.lat)) {
      await onLocationUpdated();
    }
  }
}

async function onLocationUpdated() {
  if (!hasCityCountry.value) {
    building.value.long = undefined;
    building.value.lat = undefined;
    onLongLatUpdated();
    return;
  }
  try {
    loadingGeo.value = true;
    const res = await geocoderApi.forwardGeocode({
      query: building.value.city,
      limit: 1,
      countries: building.value.country,
    });
    if (res.features && res.features.length > 0 && res.features[0]?.geometry.type === 'Point') {
      building.value.long = res.features[0].geometry.coordinates[0];
      building.value.lat = res.features[0].geometry.coordinates[1];
    } else {
      building.value.long = undefined;
      building.value.lat = undefined;
    }
  } catch (err) {
    console.error(err);
    building.value.long = undefined;
    building.value.lat = undefined;
  } finally {
    loadingGeo.value = false;
  }
  onLongLatUpdated();
}

function onLongLatUpdated() {
  if (!hasLongLat.value) {
    building.value.altitude = undefined;
    building.value.climate_zone = undefined;
    return;
  }
  loadingAlt.value = true;
  void Promise.all([
    contrib
      .fetchAltitude(building.value.long, building.value.lat)
      .then((res) => {
        building.value.altitude = res.altitude;
      })
      .catch(() => {
        building.value.altitude = undefined;
      }),
    contrib
      .fetchClimateZone(building.value.long, building.value.lat)
      .then((res) => {
        building.value.climate_zone = res.name;
      })
      .catch(() => {
        building.value.climate_zone = undefined;
      }),
  ]).finally(() => (loadingAlt.value = false));
}

function onDuplicateSpace(i: number) {
  if (!building.value.spaces) return;
  contrib.addSpace(building.value.identifier, building.value.spaces[i]);
  notifyInfo('Space duplicated');
}

function onAddSpace() {
  contrib.addSpace(building.value.identifier);
  notifyInfo('New space added');
}

function onDeleteSpace(i: number) {
  contrib.deleteSpace(building.value.identifier, i);
  notifyInfo('Space deleted');
}

function onGreenCertifiedUpdated() {
  if (building.value.green_certified === 'yes') {
    building.value.certifications = [{} as Certification];
  } else {
    building.value.certifications = [];
  }
}

function onRenovationUpdated() {
  if (building.value.renovation !== 'yes') {
    building.value.renovation_year = undefined;
    building.value.renovation_details = undefined;
  }
}

function onBuildingTypeChange() {
  if (building.value.type !== 'other') {
    building.value.other_type = undefined;
  }
}

function onOutdoorEnvChange() {
  if (building.value.outdoor_env !== 'other') {
    building.value.other_outdoor_env = undefined;
  }
}
</script>

<template>
  <div>
    <q-input
      v-model="building.identifier"
      filled
      :label="$t('study.building.identifier')"
      :hint="$t('study.building.identifier_hint')"
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
          :label="$t('study.building.type')"
          :hint="$t('study.building.type_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.special_population"
          :options="populationOptions"
          filled
          emit-value
          map-options
          :label="$t('study.building.special_population')"
          :hint="$t('study.building.special_population_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.outdoor_env"
          :options="outdoorEnvOptions"
          filled
          emit-value
          map-options
          :label="$t('study.building.outdoor_env')"
          :hint="$t('study.building.outdoor_env_hint')"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="building.construction_year"
          filled
          type="number"
          :label="$t('study.building.construction_year')"
          :hint="$t('study.building.construction_year_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="building.renovation_year"
          filled
          type="number"
          :label="$t('study.building.renovation_year')"
          :hint="$t('study.building.renovation_year_hint')"
        />
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-select
          v-model="building.mechanical_ventilation"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.building.mechanical_ventilation')"
          :hint="$t('study.building.mechanical_ventilation_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.operable_windows"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.building.operable_windows')"
          :hint="$t('study.building.operable_windows_hint')"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.smoking"
          :options="yesNoOptions"
          filled
          emit-value
          map-options
          :label="$t('study.building.smoking')"
          :hint="$t('study.building.smoking_hint')"
        />
      </div>
    </div>

    <div class="text-bold q-mb-md">Location</div>
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model="building.city"
          filled
          :label="$t('study.building.city')"
          :hint="$t('study.building.city_hint')"
          :debounce="500"
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
          :label="$t('study.building.country')"
          :hint="$t('study.building.country_hint')"
          @update:model-value="onLocationUpdated"
        />
      </div>
      <div class="col">
        <q-input
          v-model="building.postcode"
          filled
          :label="$t('study.building.postcode')"
          :hint="$t('study.building.postcode_hint')"
          :debounce="500"
          @update:model-value="onLocationUpdated"
        />
      </div>
    </div>
    <div v-if="hasCityCountry" class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="building.longitude"
          type="number"
          filled
          :label="$t('study.building.longitude')"
          :hint="$t('study.building.longitude_hint')"
          :disable="loadingGeo"
          @update:model-value="onLongLatUpdated"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="building.latitude"
          type="number"
          filled
          :label="$t('study.building.latitude')"
          :hint="$t('study.building.latitude_hint')"
          :disable="loadingGeo"
          @update:model-value="onLongLatUpdated"
        />
      </div>
    </div>
    <div v-if="hasLongLat" class="row q-col-gutter-md q-mb-md">
      <div class="col">
        <q-input
          v-model.number="building.altitude"
          type="number"
          filled
          :label="$t('study.building.altitude')"
          :hint="$t('study.building.altitude_hint')"
          :disable="loadingAlt"
        />
      </div>
      <div class="col">
        <q-select
          v-model="building.climate_zone"
          :options="climateOptions"
          filled
          emit-value
          map-options
          :label="$t('study.building.climate_zone')"
          :hint="$t('study.building.climate_zone_hint')"
          :disable="loadingAlt"
        />
      </div>
    </div>
    <div v-if="loadingAlt">
      <q-spinner-dots />
    </div>

    <div class="text-bold q-mb-md">Certification</div>
    <div class="q-mb-md">
      <q-select
        v-model="building.green_certified"
        :options="yesNoOptions"
        filled
        emit-value
        map-options
        :label="$t('study.building.green_certified')"
        :hint="$t('study.building.green_certified_hint')"
        @update:model-value="onGreenCertifiedUpdated"
      />
    </div>

    <div
      v-if="building.certifications?.length"
      class="row q-col-gutter-md q-mb-md"
    >
      <div class="col">
        <q-input
          v-model.number="building.certifications[0].program"
          filled
          :label="$t('study.building.certification_program')"
          :hint="$t('study.building.certification_program_hint')"
        />
      </div>
      <div class="col">
        <q-input
          v-model.number="building.certifications[0].level"
          filled
          :label="$t('study.building.certification_level')"
          :hint="$t('study.building.certification_level_hint')"
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
                      `${building.spaces ? building.spaces[i].identifier : i}`
                    }}
                  </template>
                  <space-form
                    v-model="building.spaces[i]"
                    :building="building"
                    class="q-mt-md"
                  />
                </q-expansion-item>
              </q-item-section>
              <q-item-section side>
                <q-btn
                  rounded
                  dense
                  flat
                  color="negative"
                  :title="$t('delete')"
                  icon="delete"
                  class="q-ml-xs"
                  @click="onDeleteSpace(i)"
                />
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

<script lang="ts">
export default defineComponent({
  name: 'BuildingForm',
});
</script>
<script setup lang="ts">
import {
  climateOptions,
  buildingTypeOptions,
  outdoorEnvOptions,
  populationOptions,
  countryOptions,
  yesNoOptions,
} from 'src/utils/options';
import { geocoderApi } from 'src/utils/geocoder';
import { Building, Certification } from 'src/models';
import SpaceForm from 'src/components/contribute/SpaceForm.vue';

const contrib = useContributeStore();

interface Props {
  modelValue: Building;
}
const props = defineProps<Props>();

const building = ref(props.modelValue);
const loadingGeo = ref(false);
const loadingAlt = ref(false);

watch(() => props.modelValue, (val) => {
  building.value = val;
  onGreenCertifiedUpdated();
});

const hasCityCountry = computed(
  () => building.value.city && building.value.country,
);
const hasLongLat = computed(
  () => building.value.longitude && building.value.latitude,
);

async function onLocationUpdated() {
  if (!hasCityCountry.value) {
    building.value.longitude = undefined;
    building.value.latitude = undefined;
    onLongLatUpdated();
    return;
  }
  try {
    const res = await geocoderApi.forwardGeocode({
      query: building.value.city,
      limit: 1,
      countries: [building.value.country],
    });
    if (res.features && res.features.length > 0 && res.features[0].center) {
      building.value.longitude = res.features[0].center[0];
      building.value.latitude = res.features[0].center[1];
    } else {
      building.value.longitude = null;
      building.value.latitude = null;
    }
  } catch (err) {
    console.error(err);
    building.value.longitude = null;
    building.value.latitude = null;
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
  Promise.all([
    contrib
      .fetchAltitude(building.value.longitude, building.value.latitude)
      .then((res) => {
        building.value.altitude = res.altitude;
      }),
    contrib
      .fetchClimateZone(building.value.longitude, building.value.latitude)
      .then((res) => {
        building.value.climate_zone = res.name;
      }),
  ]).finally(() => (loadingAlt.value = false));
}

function onAddSpace() {
  contrib.addSpace(building.value.identifier);
}

function onDeleteSpace(i: number) {
  contrib.deleteSpace(building.value.identifier, i);
}

function onGreenCertifiedUpdated() {
  if (building.value.green_certified === 'yes') {
    building.value.certifications = [{} as Certification];
  } else {
    building.value.certifications = [];
  }
}
</script>

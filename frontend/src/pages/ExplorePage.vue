<template>
  <q-page>
    <q-toolbar class="bg-accent text-white">
      
    <div>
      This section is under construction. For suggestions of useful plots and features, please file a 
      <a
        href="https://github.com/EPFL-ENAC/hobel-iaqdb/issues"
        target="_blank"
        class="text-white text-bold epfl"
        >GitHub issue <q-icon name="arrow_outward" /></a
      >.
    </div>
  </q-toolbar>
    <div class="q-pa-md">
      <div class="row q-col-gutter-md">
        <div class="col-12 col-sm-12 col-md-6">
          <DummyCandlestickChart :height="200"/>
        </div>
        <div class="col-12 col-sm-12 col-md-6">
          <DummyBarChart :height="200"/>
        </div>
      </div>
      <div class="row q-col-gutter-md">
        <div class="col-12">
          <DummyLineChart :height="200"/>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import DummyCandlestickChart from 'src/components/plots/DummyCandlestickChart.vue';
import DummyBarChart from 'src/components/plots/DummyBarChart.vue';
import DummyLineChart from 'src/components/plots/DummyLineChart.vue';
</script>

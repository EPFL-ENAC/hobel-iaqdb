<template>
  <section class="explore-chapter explore-section" :aria-labelledby="headingId">
    <div class="explore-container">
      <h2 :id="headingId" class="explore-chapter__title">{{ title }}</h2>
      <p v-if="lead" class="explore-chapter__lead">{{ lead }}</p>
      <div class="explore-chapter__figures">
        <slot />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
/** A chapter of the explore page: a heading, its lead, then its rows of figures. */
interface Props {
  title: string;
  lead?: string;
}

withDefaults(defineProps<Props>(), { lead: '' });
const headingId = useId();
</script>

<style scoped lang="scss">
.explore-chapter {
  background: $grey-1;
  border-top: 1px solid $grey-4;
}

// chapters run on as one grey area: only the hero is set apart, and the
// previous chapter's bottom padding is the only gap between two of them
.explore-chapter + .explore-chapter {
  border-top: 0;
  padding-top: 0;
}

.explore-chapter__title {
  font-size: clamp(1.5rem, 1.2rem + 1vw, 2.25rem);
  font-weight: 400;
  line-height: 1.2;
  letter-spacing: -0.01em;
  color: $grey-10;
  margin: 0 0 24px;
}

.explore-chapter__lead {
  font-size: 1.0625rem;
  line-height: 1.7;
  color: $grey-10;
  max-width: 52ch;
  margin: 0 0 40px;
}

.explore-chapter__figures {
  display: flex;
  flex-direction: column;
  gap: 40px;

  @media (max-width: $breakpoint-sm-max) {
    gap: 24px;
  }
}
</style>

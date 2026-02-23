<template>
  <v-container class="home-page py-8">
    <!-- Project name + description -->
    <v-row
        align="start"
        class="mb-4"
        justify="space-between"
    >
      <!-- Left: Text -->
      <v-col
          class="text-left text-md-left mb-4 mb-md-0"
          cols="12"
          md="7"
      >
        <h1 class="text-h4 font-weight-bold mb-1">
          {{ $t('homepage.title') }}
        </h1>
        <h2 class="text-h6 text-primary mb-2">
          {{ $t('homepage.subtitle') }}
        </h2>
        <p class="text-body-1 text-medium-emphasis mb-0">
          {{ $t('homepage.description') }}
        </p>
      </v-col>

      <!-- Right: Image -->
      <v-col
          class="d-flex justify-center justify-md-end"
          cols="12"
          md="5"
      >
        <v-img
            alt="HEAR-UI illustration"
            class="img-hero"
            contain
            max-width="300"
            src="assets/images/hero.png"
        />
      </v-col>
    </v-row>
    <v-divider class="my-6 home-divider" />

    <!-- About Prediction Models -->
    <v-row class="mt-2">
      <v-col>
        <h2 class="text-h6 font-weight-bold mb-2">{{ $t('predictions_home.about.title') }}</h2>
        <p class="text-body-1 text-medium-emphasis">
          {{ $t('predictions_home.about.description') }}
        </p>
      </v-col>
    </v-row>

    <v-divider class="my-6" />

    <!-- How to get a prediction -->
    <v-row>
      <v-col>
        <h2 class="text-h6 font-weight-bold mb-2">{{ $t('predictions_home.process.title') }}</h2>
        <v-timeline align="start" class="mt-4" density="compact" side="end">
          <v-timeline-item dot-color="primary" fill-dot icon="mdi-magnify" size="small">
            <div class="d-flex">
              <strong class="me-4">{{ $t('predictions_home.process.step1.title') }}</strong>
              <div>{{ $t('predictions_home.process.step1.description') }}</div>
            </div>
          </v-timeline-item>
          <v-timeline-item dot-color="primary" fill-dot icon="mdi-account-plus" size="small">
            <div class="d-flex">
              <strong class="me-4">{{ $t('predictions_home.process.step2.title') }}</strong>
              <div>{{ $t('predictions_home.process.step2.description') }}</div>
            </div>
          </v-timeline-item>
          <v-timeline-item dot-color="primary" fill-dot icon="mdi-account-details" size="small">
            <div class="d-flex">
              <strong class="me-4">{{ $t('predictions_home.process.step3.title') }}</strong>
              <div>{{ $t('predictions_home.process.step3.description') }}</div>
            </div>
          </v-timeline-item>
          <v-timeline-item dot-color="primary" fill-dot icon="mdi-creation" size="small">
            <div class="d-flex">
              <strong class="me-4">{{ $t('predictions_home.process.step4.title') }}</strong>
              <div>{{ $t('predictions_home.process.step4.description') }}</div>
            </div>
          </v-timeline-item>
        </v-timeline>
      </v-col>
    </v-row>

    <!-- CTA Button to Predictions -->
    <div class="d-flex justify-center mt-8 mb-4">
      <v-btn
          :to="{ name: 'PredictionsHome' }"
          color="primary"
          prepend-icon="mdi-creation"
          size="large"
          variant="elevated"
      >
        {{ $t('homepage.goto_predictions') }}
      </v-btn>
    </div>
  </v-container>
</template>

<script>
export default {
  name: 'HomePage',
};
</script>

<style scoped>
.home-page {
  max-width: 960px;
  margin: 0 auto;
}

/* Card base */
.home-card {
  height: 100%;
  border-width: 2px;
  border-style: solid;
  box-shadow: 0 0 22px rgba(var(--v-theme-primary), 0.25) !important;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
  cursor: pointer;
}

/* Optional styling for the image */
.home-card-image {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

/* Hover effect (works with v-hover + Vuetify hover styles) */
.home-card:hover,
.home-card.v-card--hover {
  box-shadow: 0 6px 28px rgba(var(--v-theme-primary), 0.45) !important;
  transform: translateY(-3px);
}

.home-divider {
  margin: 12px 0 48px 0 !important;
}

.img-hero {
  border-radius: 1%;
}

.home-card .v-card-subtitle {
  white-space: normal !important;
}

.home-card .v-card-title {
  white-space: normal !important;
  padding-bottom: 4px !important;
}

.home-card-titles {
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
}

</style>

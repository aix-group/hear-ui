<template>
  <v-container class="py-8">
    <v-sheet
        :elevation="12"
        border
        class="patient-sheet"
        rounded="lg"
    >
      <v-row justify="start" no-gutters>
        <v-btn
            :to="{ name: 'SearchPatients' }"
            color="primary"
            prepend-icon="mdi-arrow-left"
            variant="tonal"
            size="small"
        >
          {{ $t('patient_details.back') }}
        </v-btn>
      </v-row>
      <v-divider
          class="my-6"
      />

      <!-- Title -->
      <v-row justify="start" no-gutters>
        <h1>
          {{ $t('patient_details.title') }}
          <span class="text-primary">{{ displayName }}</span>
        </h1>

      </v-row>

      <v-divider
          class="my-6"
      />

      <!-- Patient details cards -->
      <v-row class="details-grid" dense>
        <v-col
          v-for="section in detailSections"
          :key="section.title"
          cols="12"
          md="6"
          class="detail-col"
        >
          <v-card class="detail-card" rounded="lg" elevation="0" variant="outlined">
            <v-card-title class="detail-card__header">
              {{ section.title }}
            </v-card-title>
            <v-card-text class="detail-card__body">
              <div v-for="item in section.items" :key="item.label" class="detail-row">
                <span class="detail-label">{{ item.label }}</span>
                <span class="detail-value">{{ item.value }}</span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>



      <v-divider
          class="my-6"
      />

      <!-- Actions -->
      <div class="d-flex flex-wrap align-center gap-3 mb-4 ms-1">

        <!-- Left group: Edit + second ear -->
        <v-btn
            color="warning"
            variant="tonal"
            prepend-icon="mdi-pencil"
            :to="{ name: 'UpdatePatient', params: { id: patient_id } }"
        >
          {{ $t('patient_details.change_patient') }}
        </v-btn>

        <v-btn
            v-if="otherEar"
            color="primary"
            variant="tonal"
            prepend-icon="mdi-ear-hearing"
            :to="{ name: 'CreatePatient', query: { copyFrom: patient_id } }"
        >
          {{ $t('patient_details.add_other_ear') }} ({{ otherEar }})
        </v-btn>

        <v-spacer />

        <!-- Right group: Delete + Predict -->
        <v-btn
            color="error"
            variant="outlined"
            prepend-icon="mdi-delete-outline"
            :disabled="!patient_id"
            @click="openDeleteDialog"
        >
          {{ $t('patient_details.delete_patient') }}
        </v-btn>

        <v-btn
            color="success"
            variant="flat"
            prepend-icon="mdi-chart-bar"
            :to="{ name: 'Prediction', params: {patient_id: patient_id}}"
        >
          {{ $t('patient_details.generate_prediction') }}
        </v-btn>
      </div>

      <v-snackbar
          v-model="updateSuccessOpen"
          color="success"
          location="top"
          timeout="2500"
      >
        {{ $t('patient_details.update_success') }}
      </v-snackbar>
      <v-snackbar
          v-model="createSuccessOpen"
          color="success"
          location="top"
          timeout="2500"
      >
        {{ $t('patient_details.create_success') }}
      </v-snackbar>

      <v-dialog
          v-model="deleteDialog"
          max-width="520"
      >
        <v-card rounded="lg">
          <v-card-title class="text-h6">
            {{ $t('patient_details.delete_confirm_title') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">
              {{ $t('patient_details.delete_confirm_body', { name: displayName }) }}
            </p>
            <v-alert
                v-if="deleteError"
                type="error"
                variant="tonal"
            >
              {{ deleteError }}
            </v-alert>
          </v-card-text>
          <v-card-actions class="justify-end">
            <v-btn
                variant="text"
                :disabled="deleteLoading"
                @click="closeDeleteDialog"
            >
              {{ $t('patient_details.delete_confirm_cancel') }}
            </v-btn>
            <v-btn
                color="error"
                variant="flat"
                :loading="deleteLoading"
                @click="confirmDelete"
            >
              {{ $t('patient_details.delete_confirm_confirm') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-sheet>
  </v-container>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref} from "vue";
import {useRoute, useRouter} from "vue-router";
import {API_BASE} from "@/lib/api";
import {useFeatureDefinitions} from "@/lib/featureDefinitions";
import {featureDefinitionsStore} from "@/lib/featureDefinitionsStore";

const route = useRoute();
const router = useRouter();

const rawId = route.params.id;
const patient_id = ref<string>(Array.isArray(rawId) ? rawId[0] : rawId ?? "");
const patient = ref<any>(null);
const deleteDialog = ref(false);
const deleteLoading = ref(false);
const deleteError = ref<string | null>(null);
const updateSuccessOpen = ref(false);
const createSuccessOpen = ref(false);

const displayName = computed(() => patient.value?.name ?? patient.value?.display_name ?? "Patient");

// Computes which ear the OTHER form should be for (flips R↔L)
const otherEar = computed<string | null>(() => {
  const side = patient.value?.input_features?.['Seiten']
  if (side === 'R') return 'L'
  if (side === 'L') return 'R'
  return null
})

const {definitions, labels, sections, sectionOrder} = useFeatureDefinitions()

const labelFor = (name: string, fallback?: string) => {
  return labels.value?.[name] ?? fallback ?? name
}

const sectionLabelFor = (name: string) => {
  return sections.value?.[name] ?? name
}

const formatValue = (value: unknown) => {
  if (value === undefined || value === null || value === "") return "—"
  if (Array.isArray(value)) return value.filter(Boolean).join(", ") || "—"
  return String(value)
}

const detailSections = computed(() => {
  const defs = definitions.value ?? []
  const input = patient.value?.input_features ?? {}

  const itemsBySection: Record<string, Array<{label: string; value: string}>> = {}

  for (const def of defs) {
    if (def?.ui_only) continue
    const section = def.section ?? "Weitere"
    const value = input?.[def.raw]
    const label = labelFor(def.normalized, def.description ?? def.raw)
    itemsBySection[section] = itemsBySection[section] ?? []
    itemsBySection[section].push({label, value: formatValue(value)})
  }

  const defaultOrder: string[] = []
  const seen: Set<string> = new Set()
  for (const def of defs) {
    const section = def.section ?? "Weitere"
    if (seen.has(section)) continue
    seen.add(section)
    defaultOrder.push(section)
  }

  const orderedSections = (sectionOrder.value?.length ? sectionOrder.value : defaultOrder).map((title) => ({
    title: sectionLabelFor(title),
    items: itemsBySection[title] ?? []
  }))

  const orderForFilter = sectionOrder.value?.length ? sectionOrder.value : defaultOrder
  const otherSections = Object.keys(itemsBySection)
    .filter((title) => !orderForFilter.includes(title))
    .sort()
    .map((title) => ({title: sectionLabelFor(title), items: itemsBySection[title]}))

  return [...orderedSections, ...otherSections]
    .filter((section) => section.items.length > 0)
    .filter((section) => section.title !== "Weitere")
})

const openDeleteDialog = () => {
  deleteError.value = null;
  deleteDialog.value = true;
};

const closeDeleteDialog = () => {
  if (!deleteLoading.value) {
    deleteDialog.value = false;
  }
};

const confirmDelete = async () => {
  if (!patient_id.value) {
    deleteError.value = "Missing patient id.";
    return;
  }

  deleteLoading.value = true;
  deleteError.value = null;

  try {
    const response = await fetch(
        `${API_BASE}/api/v1/patients/${encodeURIComponent(patient_id.value)}`,
        {
          method: "DELETE",
          headers: {
            accept: "application/json",
          },
        }
    );

    if (!response.ok) {
      let message = "Failed to delete patient.";
      try {
        const text = await response.text();
        if (text) message = text;
      } catch {
        // ignore parsing error
      }
      throw new Error(message);
    }

    deleteDialog.value = false;
    await router.push({name: "SearchPatients"});
  } catch (err: any) {
    console.error(err);
    deleteError.value = err?.message ?? "Failed to delete patient.";
  } finally {
    deleteLoading.value = false;
  }
};


onMounted(async () => {
  if (!definitions.value?.length) {
    await featureDefinitionsStore.loadDefinitions()
    await featureDefinitionsStore.loadLabels()
  }
  if (route.query.updated === '1') {
    updateSuccessOpen.value = true;
    router.replace({query: {...route.query, updated: undefined}});
  }
  if (route.query.created === '1') {
    createSuccessOpen.value = true;
    router.replace({query: {...route.query, created: undefined}});
  }

  if (!patient_id.value) {
    await router.replace({name: "NotFound"});
    return;
  }

  try {
    const response = await fetch(
        `${API_BASE}/api/v1/patients/${encodeURIComponent(patient_id.value)}`,
        {
          method: "GET",
          headers: {
            accept: "application/json",
          },
        }
    );

    if (response.status === 404) {
      await router.replace({name: "NotFound"});
      return;
    }
    if (!response.ok) throw new Error("Network error");

    patient.value = await response.json();

  } catch (err: any) {
    console.error(err);
  }
});

</script>

<style scoped>
.patient-sheet {
  padding: 32px;
  border-width: 2px;
  border-style: solid;
  border-color: rgb(var(--v-theme-primary));
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 4px 22px rgba(var(--v-theme-primary), 0.35) !important;
}

/* stack cards vertically and center them a bit */
.details-grid {
  margin-top: 8px;
  row-gap: 12px;
}

.detail-col {
  margin-bottom: 12px;
}

@media (min-width: 1280px) {
  .details-grid {
    row-gap: 8px;
  }

  .detail-col {
    margin-bottom: 6px;
  }
}

/* one “Personal details” style card */
.detail-card {
  height: 100%;
  border-radius: 16px;
  padding: 12px 16px 16px;
  box-shadow: none;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background-color: rgb(var(--v-theme-surface));
}

/* header text */
.detail-card__header {
  font-weight: 600;
  font-size: 1rem;
  padding: 4px 0 8px;
}

/* body */
.detail-card__body {
  margin-top: 4px;
  padding: 0;
}

/* rows inside the card */
.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-top: 1px dashed rgba(148, 163, 184, 0.6);
  column-gap: 16px;
}

.detail-label {
  font-size: 0.88rem;
  color: #6b7280;
}

.detail-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: #111827;
  text-align: right;
  max-width: 55%;
  word-break: break-word;
}

@media (max-width: 600px) {
  .detail-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-value {
    text-align: left;
    max-width: 100%;
  }
}
</style>

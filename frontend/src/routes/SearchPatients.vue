<template>
  <v-container class="py-8">

    <!-- SEARCH BAR -->
    <v-row
        :elevation="12"
        align="center"
        border
        class="search-box"
        rounded="lg"
    >
      <v-text-field
          v-model="search"
          :placeholder="$t('search.text')"
          density="comfortable"
          flat
          hide-details
          prepend-inner-icon="mdi-magnify"
          rounded="lg"
          variant="solo"
          autocomplete="off"
      />
    </v-row>

    <!-- Add Patient Button (below search) -->
    <div class="d-flex justify-end mt-3">
      <v-btn
          :to="{ name: 'CreatePatient' }"
          color="primary"
          density="comfortable"
          flat
          rounded="6"
          prepend-icon="mdi-account-plus"
      >
        {{ $t('search.add_new_patient') }}
      </v-btn>
    </div>

    <!-- Results -->

    <v-row
        v-if="filteredData.length > 0"
        :elevation="12"
        align="stretch"
        border
        class="search-box result_list"
        rounded="lg"
    >

      <v-col class="result_list" cols="12">
        <v-list class="result_list">
          <v-list-item
              v-for="item in filteredData"
              :key="item.id"
              :to="{ name: 'PatientDetail', params: { id: item.id } }"
              class="search-result-item"
              prepend-icon="mdi-account-box"
          >
            <v-list-item-title>
              {{ item.name }}<span v-if="formatBirthDate(item.birthDate)">, {{ formatBirthDate(item.birthDate) }}</span>
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-col>

    </v-row>

  </v-container>
</template>

<script lang="ts" setup>
import {ref, watch} from "vue";
import {API_BASE} from "@/lib/api";

const search = ref("");

const filteredData = ref<Array<{ id: string; name: string; birthYear?: number | null; birthDate?: string | null }>>([])
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const formatBirthDate = (raw: string | null | undefined): string | null => {
  if (!raw) return null
  // already DD.MM.YYYY
  if (/^\d{2}\.\d{2}\.\d{4}$/.test(raw)) return raw
  // YYYY-MM-DD (HTML date input)
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    const [y, m, d] = raw.split('-')
    return `${d}.${m}.${y}`
  }
  return raw
}

watch(search, (newValue) => {
  if (debounceTimer) clearTimeout(debounceTimer);

  debounceTimer = setTimeout(async () => {
    if (newValue.length < 1) {
      filteredData.value = [];
      return;
    }
    try {
      const response = await fetch(
          `${API_BASE}/api/v1/patients/search?q=${encodeURIComponent(newValue)}`,
          {
            method: "GET",
            headers: {
              accept: "application/json",
            },
          }
      );

      if (!response.ok) throw new Error("Network error");

      const data = await response.json();

      filteredData.value = Array.isArray(data)
          ? data.map((p: any) => ({
            id: p.id ?? p.uuid ?? "",
            name: p.name ?? p.display_name ?? "Unnamed patient",
            birthYear: p.birth_year ?? null,
            birthDate: p.birth_date ?? null,
          })).filter((p) => p.id)
          : [];

    } catch (err) {
      console.error(err);
      filteredData.value = [];
    }
  }, 200);
});


</script>

<style scoped>
.search-box {
  padding-right: 8px;
  margin: 32px 0 32px 0;
  border-radius: 10px;
  border-width: 2px;
  border-style: solid;
  border-color: rgb(var(--v-theme-primary));
  background-color: rgb(var(--v-theme-surface));
  box-shadow: 0 4px 22px rgba(var(--v-theme-primary), 0.35) !important;
}

/* LIST container with no padding */
.result_list {
  padding-left: 0 !important;
  margin-left: 0 !important;
  padding-right: 0 !important;
  margin-right: 0 !important;
}

/* each item: spacing + better layout */
.search-result-item {
  padding-left: 20px;
  padding-right: 20px;
  min-height: 72px;
  display: flex;
  align-items: center;
  font-size: 1.25rem;
}

/* lighter primary for hover */
.search-result-item:hover {
  /* very light blue tint */
  background-color: rgba(var(--v-theme-primary), 0.06) !important;
  color: rgb(var(--v-theme-primary)) !important;
}

/* Router-link active state (selected row) */
.search-result-item.v-list-item--active {
  background-color: rgba(var(--v-theme-primary), 0.06) !important;
  color: rgb(var(--v-theme-primary)) !important;
  font-weight: 500;
}

/* icon left spacing fix — compensates for removed padding */
.search-result-item .v-list-item__prepend {
  margin-left: 12px;
  margin-right: 16px;
}

/* optional: make the active icon look like your mockup */
.search-result-item.v-list-item--active .v-icon {
  background-color: rgb(var(--v-theme-primary));
  color: white;
  border-radius: 4px;
  padding: 4px;
}
</style>

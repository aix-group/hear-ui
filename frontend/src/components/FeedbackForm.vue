<template>
  <form @submit.prevent="submitFeedback" class="feedback-form">
    <div class="feedback-question">
      <p class="question-text">
        {{ $t('prediction.feedback.question') }}
      </p>
      <div class="feedback-buttons">
        <button
          type="button"
          class="feedback-btn agree"
          :class="{ active: formData.accepted === true }"
          @click="formData.accepted = true"
        >
          <v-icon size="18" class="mr-1">mdi-thumb-up-outline</v-icon>
          {{ $t('prediction.feedback.agree') }}
        </button>
        <button
          type="button"
          class="feedback-btn disagree"
          :class="{ active: formData.accepted === false }"
          @click="formData.accepted = false"
        >
          <v-icon size="18" class="mr-1">mdi-thumb-down-outline</v-icon>
          {{ $t('prediction.feedback.disagree') }}
        </button>
      </div>
    </div>

    <div class="form-group">
      <label for="comment">
        {{ $t('prediction.feedback.comment_label') }}
      </label>
      <textarea
        id="comment"
        v-model="formData.comment"
        rows="4"
        :placeholder="$t('prediction.feedback.comment_placeholder')"
        :disabled="submitting"
      ></textarea>
      <small class="hint">
        {{ $t('prediction.feedback.hint') }}
      </small>
    </div>

    <button
      type="submit"
      class="submit-btn"
      :disabled="formData.accepted === null || submitting"
    >
      <span v-if="!submitting">
          <v-icon size="18" class="mr-1">mdi-send-outline</v-icon>
          {{ $t('prediction.feedback.submit') }}
      </span>
      <span v-else class="loading-spinner">
        <span class="spinner"></span>
        {{ $t('prediction.feedback.sending') }}
      </span>
    </button>

    <p v-if="error" class="error-message">
      {{ error }}
    </p>
  </form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import i18next from 'i18next'
import { API_BASE } from '@/lib/api'

interface Props {
  predictionData: {
    prediction: number
    explanation: Record<string, number>
  }
  patientData: {
    age: number
    hearing_loss_duration: number
    implant_type: string
  }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  feedbackSubmitted: []
}>()

const formData = reactive({
  accepted: null as boolean | null,
  comment: ''
})

const submitting = ref(false)
const error = ref('')

const submitFeedback = async () => {
  if (formData.accepted === null) {
    error.value = i18next.t('prediction.feedback.required_error')
    return
  }

  submitting.value = true
  error.value = ''

  try {
    const feedbackPayload = {
      input_features: props.patientData,
      prediction: props.predictionData.prediction,
      explanation: props.predictionData.explanation,
      accepted: formData.accepted,
      comment: formData.comment || null
    }

    const response = await fetch(`${API_BASE}/api/v1/feedback/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedbackPayload),
    })

    if (!response.ok) {
      throw new Error('Feedback submission failed')
    }

    // Reset form
    formData.accepted = null
    formData.comment = ''

    emit('feedbackSubmitted')
  } catch (err) {
    console.error('Error submitting feedback:', err)
    error.value = i18next.t('prediction.feedback.submit_error')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.feedback-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.feedback-question {
  background: rgba(var(--v-theme-primary), 0.08);
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-primary), 0.28);
  border-left: 4px solid rgb(var(--v-theme-primary));
}

.question-text {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.feedback-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.feedback-btn {
  padding: 1rem;
  border: 1px solid rgba(var(--v-theme-primary), 0.25);
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: rgb(var(--v-theme-on-surface));
}

.feedback-btn .icon {
  font-size: 1.5rem;
}

.feedback-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(var(--v-theme-primary), 0.12);
  background: rgba(var(--v-theme-primary), 0.06);
}

.feedback-btn.agree.active {
  background: rgba(var(--v-theme-success), 0.16);
  border-color: rgb(var(--v-theme-success));
  color: rgb(var(--v-theme-on-surface));
}

.feedback-btn.disagree.active {
  background: rgba(var(--v-theme-error), 0.16);
  border-color: rgb(var(--v-theme-error));
  color: rgb(var(--v-theme-on-surface));
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  font-size: 1rem;
}

.form-group textarea,
.form-group input {
  padding: 0.75rem 1rem;
  border: 1px solid rgba(var(--v-theme-primary), 0.25);
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}

.form-group textarea:focus,
.form-group input:focus {
  outline: none;
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 3px rgba(var(--v-theme-primary), 0.15);
}

.form-group textarea:disabled,
.form-group input:disabled {
  background: rgba(var(--v-theme-on-surface), 0.04);
  cursor: not-allowed;
  opacity: 0.6;
}

.hint {
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.875rem;
}

.submit-btn {
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(var(--v-theme-primary), 0.25);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn .icon {
  font-size: 1.2rem;
}

.loading-spinner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.35);
  border-top-color: rgb(var(--v-theme-on-primary));
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  background: rgba(var(--v-theme-error), 0.14);
  color: rgb(var(--v-theme-on-surface));
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin: 0;
  border-left: 4px solid rgb(var(--v-theme-error));
}

@media (max-width: 768px) {
  .feedback-buttons {
    grid-template-columns: 1fr;
  }
  
  .submit-btn {
    font-size: 1rem;
    padding: 0.875rem 1.5rem;
  }
}
</style>

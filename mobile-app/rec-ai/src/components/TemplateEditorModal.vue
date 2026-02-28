<template>
  <ion-modal :is-open="isOpen" @didDismiss="$emit('close')">
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-button @click="$emit('close')">Cancel</ion-button>
        </ion-buttons>
        <ion-title>{{ templateKey ? 'Edit Template' : 'New Template' }}</ion-title>
        <ion-buttons slot="end">
          <ion-button strong @click="handleSave" color="primary">Save</ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="editor-content">
      <div class="editor-form">
        <!-- Template Name -->
        <div class="form-group">
          <label class="form-label">Template Name</label>
          <input
            v-model="name"
            type="text"
            class="form-input"
            placeholder="My Template"
            :disabled="isDefault"
          />
          <p v-if="isDefault" class="form-hint">Default templates can't be renamed. A copy will be saved.</p>
        </div>

        <!-- Accent Color -->
        <div class="form-group">
          <label class="form-label">Accent Color</label>
          <div class="color-row">
            <div class="color-swatches">
              <button
                v-for="c in presetColors"
                :key="c"
                class="swatch"
                :class="{ active: accentColor === c }"
                :style="{ background: c }"
                @click="accentColor = c"
              ></button>
            </div>
            <input v-model="accentColor" type="color" class="color-picker" />
          </div>
        </div>

        <!-- Text Color -->
        <div class="form-group">
          <label class="form-label">Text Color</label>
          <div class="color-row">
            <div class="color-swatches">
              <button
                v-for="c in textPresetColors"
                :key="c"
                class="swatch"
                :class="{ active: textColor === c }"
                :style="{ background: c }"
                @click="textColor = c"
              ></button>
            </div>
            <input v-model="textColor" type="color" class="color-picker" />
          </div>
        </div>

        <!-- Header Style -->
        <div class="form-group">
          <label class="form-label">Header Style</label>
          <div class="style-options">
            <button
              v-for="s in headerStyles"
              :key="s.value"
              class="style-btn"
              :class="{ active: headerStyle === s.value }"
              @click="headerStyle = s.value"
            >
              {{ s.label }}
            </button>
          </div>
        </div>

        <!-- Logo Upload -->
        <div class="form-group">
          <label class="form-label">Logo</label>
          <div v-if="logoPreview" class="logo-preview">
            <img :src="logoPreview" alt="Logo" />
            <button class="remove-logo" @click="removeLogo">
              <ion-icon :icon="closeCircleOutline"></ion-icon>
            </button>
          </div>
          <button v-else class="upload-logo-btn" @click="logoInputRef?.click()">
            <ion-icon :icon="imageOutline"></ion-icon>
            <span>Upload Logo</span>
          </button>
          <input
            ref="logoInputRef"
            type="file"
            accept="image/*"
            class="hidden-input"
            @change="handleLogoUpload"
          />
        </div>

        <!-- Live Preview -->
        <div class="form-group">
          <label class="form-label">Preview</label>
          <div class="preview-card">
            <div v-if="logoPreview" class="preview-logo">
              <img :src="logoPreview" alt="Logo" />
            </div>
            <div
              class="preview-header"
              :class="{
                'header-underlined': headerStyle === 'underlined',
                'header-boxed': headerStyle === 'boxed',
                'header-centered': headerStyle === 'centered'
              }"
              :style="headerPreviewStyle"
            >
              <h3 :style="{ color: textColor }">Meeting Minutes</h3>
              <p class="preview-date">February 17, 2026</p>
            </div>
            <div class="preview-body" :style="{ color: textColor }">
              <p><strong>Attendees:</strong> John, Sarah, Mike</p>
              <p>&#8226; Discussed project timeline</p>
              <p>&#8226; Reviewed quarterly goals</p>
            </div>
          </div>
        </div>

        <!-- Delete Button -->
        <button
          v-if="templateKey && !isDefault"
          class="delete-btn"
          @click="handleDelete"
        >
          <ion-icon :icon="trashOutline"></ion-icon>
          <span>Delete Template</span>
        </button>
      </div>
    </ion-content>
  </ion-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { IonModal, IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonContent, IonIcon } from '@ionic/vue';
import { closeCircleOutline, imageOutline, trashOutline } from 'ionicons/icons';
import type { PdfTemplate } from '@/services/pdfTemplates';

const props = defineProps<{
  isOpen: boolean;
  template: PdfTemplate | null;
  templateKey: string | null;
  isDefault: boolean;
  currentLogo: string | null;
}>();

const emit = defineEmits<{
  close: [];
  save: [key: string | null, template: PdfTemplate, logo: string | null, logoChanged: boolean];
  delete: [key: string];
}>();

const name = ref('');
const accentColor = ref('#16a34a');
const textColor = ref('#111827');
const headerStyle = ref<PdfTemplate['headerStyle']>('underlined');
const logoPreview = ref<string | null>(null);
const logoChanged = ref(false);
const logoInputRef = ref<HTMLInputElement | null>(null);

const presetColors = ['#16a34a', '#2563eb', '#9333ea', '#dc2626', '#ea580c', '#0891b2'];
const textPresetColors = ['#111827', '#374151', '#1e293b', '#1f2937', '#0f172a', '#44403c'];
const headerStyles = [
  { value: 'simple' as const, label: 'Simple' },
  { value: 'underlined' as const, label: 'Underlined' },
  { value: 'boxed' as const, label: 'Boxed' },
  { value: 'centered' as const, label: 'Centered' }
];

const headerPreviewStyle = computed(() => {
  const styles: Record<string, string> = {};
  if (headerStyle.value === 'underlined') {
    styles.borderBottom = `3px solid ${accentColor.value}`;
  }
  if (headerStyle.value === 'boxed') {
    styles.background = `${accentColor.value}15`;
    styles.borderRadius = '8px';
    styles.padding = '12px';
  }
  return styles;
});

watch(() => props.isOpen, (open) => {
  if (open) {
    if (props.template) {
      name.value = props.template.name;
      accentColor.value = props.template.accentColor;
      textColor.value = props.template.textColor;
      headerStyle.value = props.template.headerStyle;
    } else {
      name.value = '';
      accentColor.value = '#16a34a';
      textColor.value = '#111827';
      headerStyle.value = 'underlined';
    }
    logoPreview.value = props.currentLogo;
    logoChanged.value = false;
  }
});

function handleLogoUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  if (file.size > 2 * 1024 * 1024) {
    input.value = '';
    return;
  }

  const reader = new FileReader();
  reader.onloadend = () => {
    logoPreview.value = reader.result as string;
    logoChanged.value = true;
  };
  reader.readAsDataURL(file);
  input.value = '';
}

function removeLogo() {
  logoPreview.value = null;
  logoChanged.value = true;
}

function handleSave() {
  const templateName = name.value.trim() || 'Custom Template';
  const template: PdfTemplate = {
    name: templateName,
    accentColor: accentColor.value,
    textColor: textColor.value,
    headerStyle: headerStyle.value,
    isDefault: false
  };
  emit('save', props.isDefault ? null : props.templateKey, template, logoPreview.value, logoChanged.value);
}

function handleDelete() {
  if (props.templateKey) {
    emit('delete', props.templateKey);
  }
}
</script>

<style scoped>
.editor-content {
  --background: var(--app-bg);
}

.editor-form {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--app-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input {
  padding: 12px 14px;
  border: 1px solid var(--app-border);
  border-radius: var(--radius-lg);
  background: var(--app-surface);
  color: var(--app-text);
  font-size: 15px;
  outline: none;
}

.form-input:focus {
  border-color: var(--app-primary);
}

.form-input:disabled {
  opacity: 0.5;
}

.form-hint {
  font-size: 12px;
  color: var(--app-text-muted);
  margin: 0;
}

.color-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-swatches {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.swatch {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 3px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
}

.swatch.active {
  border-color: var(--app-text);
  transform: scale(1.1);
}

.color-picker {
  width: 36px;
  height: 36px;
  border: 1px solid var(--app-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  padding: 2px;
  background: var(--app-surface);
}

.style-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.style-btn {
  padding: 10px;
  border: 1.5px solid var(--app-border);
  border-radius: var(--radius-lg);
  background: var(--app-surface);
  color: var(--app-text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.style-btn.active {
  border-color: var(--app-primary);
  background: var(--app-primary-ultra-light);
  color: var(--app-primary);
}

/* Logo */
.logo-preview {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 12px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--radius-lg);
}

.logo-preview img {
  max-height: 50px;
  max-width: 180px;
  object-fit: contain;
}

.remove-logo {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  color: var(--ion-color-danger);
  cursor: pointer;
}

.remove-logo ion-icon {
  font-size: 24px;
}

.upload-logo-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border: 1.5px dashed var(--app-border);
  border-radius: var(--radius-lg);
  background: var(--app-surface);
  color: var(--app-text-muted);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.upload-logo-btn ion-icon {
  font-size: 20px;
}

.hidden-input {
  display: none;
}

/* Preview */
.preview-card {
  background: #ffffff;
  border: 1px solid var(--app-border);
  border-radius: var(--radius-lg);
  padding: 16px;
  overflow: hidden;
}

.preview-logo {
  margin-bottom: 12px;
}

.preview-logo img {
  max-height: 36px;
  max-width: 120px;
  object-fit: contain;
}

.preview-header {
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.preview-header.header-centered {
  text-align: center;
}

.preview-header h3 {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 4px;
}

.preview-date {
  font-size: 11px;
  color: #9ca3af;
  margin: 0;
}

.preview-body {
  font-size: 12px;
  line-height: 1.6;
}

.preview-body p {
  margin: 2px 0;
}

/* Delete */
.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-lg);
  background: rgba(239, 68, 68, 0.06);
  color: var(--ion-color-danger);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.delete-btn ion-icon {
  font-size: 18px;
}
</style>

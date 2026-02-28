<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="detail-page">
        <!-- Header -->
        <header class="page-header">
          <button class="header-btn" @click="router.back()">
            <ion-icon :icon="chevronBackOutline"></ion-icon>
          </button>
          <span class="header-title">Recording</span>
          <button class="header-btn" @click="showOptions = true">
            <ion-icon :icon="ellipsisHorizontalOutline"></ion-icon>
          </button>
        </header>

        <!-- Loading -->
        <div v-if="loading && !recording" class="loading-state">
          <ion-spinner name="crescent"></ion-spinner>
        </div>

        <!-- Not Found -->
        <div v-else-if="!recording" class="empty-state">
          <div class="empty-icon-wrap">
            <ion-icon :icon="alertCircleOutline"></ion-icon>
          </div>
          <h3>Recording not found</h3>
          <button class="link-btn" @click="router.push('/recordings')">Back to library</button>
        </div>

        <!-- Content -->
        <template v-else>
          <!-- Title Section -->
          <div class="title-section">
            <h1>{{ recording.title }}</h1>
            <div class="meta-row">
              <div class="meta-chip">
                <ion-icon :icon="calendarOutline"></ion-icon>
                <span>{{ formatDate(recording.createdAt) }}</span>
              </div>
              <div class="meta-chip">
                <ion-icon :icon="timeOutline"></ion-icon>
                <span>{{ formatDuration(recording.duration) }}</span>
              </div>
              <div class="status-chip" :class="recording.status">
                {{ formatStatus(recording.status) }}
              </div>
            </div>
          </div>

          <!-- Compact Audio Player -->
          <div class="player-section" v-if="recording.audioUrl">
            <button class="player-btn" @click="togglePlay">
              <ion-icon :icon="isPlaying ? pauseOutline : playOutline"></ion-icon>
            </button>
            <div class="player-body">
              <div class="player-bar" @click="seekAudio">
                <div class="bar-fill" :style="{ width: `${progress}%` }"></div>
                <div class="bar-thumb" :style="{ left: `${progress}%` }"></div>
              </div>
              <div class="player-times">
                <span>{{ currentTime }}</span>
                <span>{{ totalTime }}</span>
              </div>
            </div>
            <audio ref="audioRef" :src="recording.audioUrl" @timeupdate="updateProgress" @loadedmetadata="onLoaded" @ended="isPlaying = false"></audio>
          </div>

          <!-- AI Actions -->
          <div class="ai-section">
            <h2 class="section-label">AI Tools</h2>
            <div class="ai-grid">
              <button
                class="ai-card"
                :class="{ done: recording.transcript, active: processingAction === 'transcribe' || recording.status === 'transcribing' }"
                :disabled="processing || !!recording.transcript || recording.status === 'transcribing'"
                @click="handleTranscribe"
              >
                <div class="ai-card-icon" :class="{ done: recording.transcript }">
                  <ion-spinner v-if="processingAction === 'transcribe' || recording.status === 'transcribing'" name="crescent"></ion-spinner>
                  <ion-icon v-else-if="recording.transcript" :icon="checkmarkOutline"></ion-icon>
                  <ion-icon v-else :icon="textOutline"></ion-icon>
                </div>
                <span class="ai-card-label">{{ recording.status === 'transcribing' ? 'Transcribing...' : recording.transcript ? 'Transcribed' : 'Transcribe' }}</span>
              </button>

              <button
                class="ai-card"
                :class="{ done: recording.summary, active: processingAction === 'summarize' }"
                :disabled="processing || !recording.transcript || !!recording.summary"
                @click="handleSummarize"
              >
                <div class="ai-card-icon" :class="{ done: recording.summary }">
                  <ion-spinner v-if="processingAction === 'summarize'" name="crescent"></ion-spinner>
                  <ion-icon v-else-if="recording.summary" :icon="checkmarkOutline"></ion-icon>
                  <ion-icon v-else :icon="sparklesOutline"></ion-icon>
                </div>
                <span class="ai-card-label">{{ recording.summary ? 'Summarized' : 'Summarize' }}</span>
              </button>

              <button
                class="ai-card"
                :class="{ done: recording.minutes, active: processingAction === 'minutes' }"
                :disabled="processing || !recording.transcript || !!recording.minutes"
                @click="handleMinutes"
              >
                <div class="ai-card-icon" :class="{ done: recording.minutes }">
                  <ion-spinner v-if="processingAction === 'minutes'" name="crescent"></ion-spinner>
                  <ion-icon v-else-if="recording.minutes" :icon="checkmarkOutline"></ion-icon>
                  <ion-icon v-else :icon="listOutline"></ion-icon>
                </div>
                <span class="ai-card-label">{{ recording.minutes ? 'Minutes Ready' : 'Minutes' }}</span>
              </button>
            </div>
          </div>

          <!-- Content Tabs -->
          <div class="content-section" v-if="recording.transcript || recording.summary || recording.minutes">
            <div class="content-tabs">
              <button
                v-for="tab in availableTabs"
                :key="tab.key"
                class="content-tab"
                :class="{ active: activeTab === tab.key }"
                @click="activeTab = tab.key"
              >
                <ion-icon :icon="tab.icon"></ion-icon>
                <span>{{ tab.label }}</span>
              </button>
            </div>

            <!-- Tab Content -->
            <div class="tab-content">
              <div class="tab-header">
                <h3>{{ activeTabLabel }}</h3>
                <div class="tab-actions">
                  <button class="action-btn" @click="copyActiveContent" title="Copy">
                    <ion-icon :icon="copyOutline"></ion-icon>
                  </button>
                  <button
                    v-if="activeTab === 'summary' || activeTab === 'minutes'"
                    class="action-btn"
                    :disabled="generatingPDF"
                    @click="activeTab === 'minutes' ? downloadMinutesPDF() : downloadSummaryPDF()"
                    title="Download PDF"
                  >
                    <ion-spinner v-if="generatingPDF" name="crescent" style="width:16px;height:16px"></ion-spinner>
                    <ion-icon v-else :icon="downloadOutline"></ion-icon>
                  </button>
                </div>
              </div>

              <!-- Template Selector (Minutes only) -->
              <div v-if="activeTab === 'minutes'" class="template-bar">
                <div class="template-selector">
                  <label>Template:</label>
                  <select v-model="selectedTemplate" class="template-select">
                    <option v-for="(tmpl, key) in templates" :key="key" :value="key">{{ tmpl.name }}</option>
                  </select>
                </div>
                <div class="template-actions">
                  <button class="icon-btn" @click="openTemplateEditor(selectedTemplate)" title="Edit">
                    <ion-icon :icon="createOutline"></ion-icon>
                  </button>
                  <button class="icon-btn accent" @click="openTemplateEditor()" title="New">
                    <ion-icon :icon="addOutline"></ion-icon>
                  </button>
                </div>
              </div>

              <div class="tab-body formatted" v-if="activeTab === 'transcript'" v-html="renderMarkdown(recording.transcript!)"></div>
              <div class="tab-body formatted" v-else-if="activeTab === 'summary'" v-html="renderMarkdown(recording.summary!)"></div>
              <div class="tab-body formatted" v-else-if="activeTab === 'minutes'" v-html="renderMarkdown(recording.minutes!)"></div>
            </div>
          </div>
        </template>
      </div>

      <!-- Options Sheet -->
      <ion-action-sheet
        :is-open="showOptions"
        :buttons="optionButtons"
        @didDismiss="showOptions = false"
      ></ion-action-sheet>

      <!-- Delete Alert -->
      <ion-alert
        :is-open="showDeleteAlert"
        header="Delete Recording?"
        message="This action cannot be undone."
        :buttons="deleteButtons"
        @didDismiss="showDeleteAlert = false"
      ></ion-alert>
      <!-- Template Editor Modal -->
      <TemplateEditorModal
        :is-open="showTemplateEditor"
        :template="editingTemplateKey ? templates[editingTemplateKey] || null : null"
        :template-key="editingTemplateKey"
        :is-default="editingTemplateKey ? !!templates[editingTemplateKey]?.isDefault : false"
        :current-logo="logoBase64"
        @close="showTemplateEditor = false"
        @save="handleTemplateSave"
        @delete="handleTemplateDelete"
      />
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { IonPage, IonContent, IonIcon, IonSpinner, IonActionSheet, IonAlert, toastController } from '@ionic/vue';
import {
  chevronBackOutline, ellipsisHorizontalOutline, playOutline, pauseOutline,
  textOutline, sparklesOutline, listOutline, checkmarkOutline, copyOutline,
  alertCircleOutline, shareOutline, trashOutline, calendarOutline, timeOutline,
  downloadOutline, createOutline, addOutline
} from 'ionicons/icons';
import { useRecordingsStore } from '@/stores/recordings';
import { loadTemplates, saveCustomTemplates, loadLogo, saveLogo, removeLogo } from '@/services/pdfTemplates';
import type { PdfTemplate } from '@/services/pdfTemplates';
import { generateMinutesPdf, generateSummaryPdf } from '@/services/pdfGenerator';
import TemplateEditorModal from '@/components/TemplateEditorModal.vue';

const router = useRouter();
const route = useRoute();
const recordingsStore = useRecordingsStore();

const showOptions = ref(false);
const showDeleteAlert = ref(false);
const processingAction = ref('');
const activeTab = ref('transcript');

// Audio
const audioRef = ref<HTMLAudioElement | null>(null);
const isPlaying = ref(false);
const progress = ref(0);
const currentTime = ref('0:00');
const totalTime = ref('0:00');

// PDF & Templates
const templates = ref<Record<string, PdfTemplate>>({});
const selectedTemplate = ref('professional');
const generatingPDF = ref(false);
const logoBase64 = ref<string | null>(null);
const showTemplateEditor = ref(false);
const editingTemplateKey = ref<string | null>(null);

const recording = computed(() => recordingsStore.currentRecording);
const loading = computed(() => recordingsStore.loading);
const processing = computed(() => recordingsStore.processing);

const availableTabs = computed(() => {
  const tabs = [];
  if (recording.value?.transcript) tabs.push({ key: 'transcript', label: 'Transcript', icon: textOutline });
  if (recording.value?.summary) tabs.push({ key: 'summary', label: 'Summary', icon: sparklesOutline });
  if (recording.value?.minutes) tabs.push({ key: 'minutes', label: 'Minutes', icon: listOutline });
  return tabs;
});

const activeTabLabel = computed(() => {
  return availableTabs.value.find(t => t.key === activeTab.value)?.label || 'Content';
});

const optionButtons = [
  { text: 'Share', icon: shareOutline, handler: handleShare },
  { text: 'Delete', icon: trashOutline, role: 'destructive', handler: () => { showDeleteAlert.value = true; } },
  { text: 'Cancel', role: 'cancel' }
];

const deleteButtons = [
  { text: 'Cancel', role: 'cancel' },
  {
    text: 'Delete',
    role: 'destructive',
    handler: async () => {
      const id = route.params.id as string;
      await recordingsStore.deleteRecording(id);
      router.replace('/recordings');
    }
  }
];

const pollInterval = ref<number | null>(null);

onMounted(async () => {
  const id = route.params.id as string;
  recordingsStore.fetchRecording(id);
  templates.value = await loadTemplates();
  logoBase64.value = await loadLogo();
});

onUnmounted(() => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value);
    pollInterval.value = null;
  }
});

watch(() => route.params.id, (id) => {
  if (id) recordingsStore.fetchRecording(id as string);
});

// Poll for updates while transcription is in progress
watch(recording, (rec) => {
  if (rec && (rec.status === 'transcribing' || rec.status === 'pending') && !pollInterval.value) {
    pollInterval.value = window.setInterval(async () => {
      const updated = await recordingsStore.fetchRecording(rec._id);
      if (updated && updated.status !== 'transcribing' && updated.status !== 'pending') {
        clearInterval(pollInterval.value!);
        pollInterval.value = null;
      }
    }, 3000);
  } else if (rec && rec.status !== 'transcribing' && rec.status !== 'pending' && pollInterval.value) {
    clearInterval(pollInterval.value);
    pollInterval.value = null;
  }
}, { immediate: true });

watch(recording, (rec) => {
  if (rec) {
    if (rec.transcript && !rec.summary && !rec.minutes) activeTab.value = 'transcript';
    else if (rec.summary) activeTab.value = 'summary';
    else if (rec.minutes) activeTab.value = 'minutes';
  }
});

function togglePlay() {
  if (!audioRef.value) return;
  if (isPlaying.value) {
    audioRef.value.pause();
  } else {
    audioRef.value.play();
  }
  isPlaying.value = !isPlaying.value;
}

function updateProgress() {
  if (!audioRef.value) return;
  const { currentTime: ct, duration } = audioRef.value;
  progress.value = (ct / duration) * 100;
  currentTime.value = formatTime(ct);
}

function onLoaded() {
  if (audioRef.value) {
    totalTime.value = formatTime(audioRef.value.duration);
  }
}

function seekAudio(e: MouseEvent) {
  if (!audioRef.value) return;
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
  const percent = (e.clientX - rect.left) / rect.width;
  audioRef.value.currentTime = percent * audioRef.value.duration;
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

async function handleTranscribe() {
  if (!recording.value) return;
  processingAction.value = 'transcribe';
  await recordingsStore.transcribeRecording(recording.value._id);
  processingAction.value = '';
  activeTab.value = 'transcript';
}

async function handleSummarize() {
  if (!recording.value) return;
  processingAction.value = 'summarize';
  await recordingsStore.summarizeRecording(recording.value._id);
  processingAction.value = '';
  activeTab.value = 'summary';
}

async function handleMinutes() {
  if (!recording.value) return;
  processingAction.value = 'minutes';
  await recordingsStore.generateMinutes(recording.value._id);
  processingAction.value = '';
  activeTab.value = 'minutes';
}

async function handleShare() {
  if (!recording.value) return;
  const text = `${recording.value.title}\n\n${recording.value.summary || recording.value.transcript || ''}`;
  if (navigator.share) {
    navigator.share({ title: recording.value.title, text });
  } else {
    await navigator.clipboard.writeText(text);
  }
}

async function copyActiveContent() {
  if (!recording.value) return;
  let text = '';
  if (activeTab.value === 'transcript') text = recording.value.transcript || '';
  else if (activeTab.value === 'summary') text = recording.value.summary || '';
  else if (activeTab.value === 'minutes') text = recording.value.minutes || '';

  await navigator.clipboard.writeText(text);
  const toast = await toastController.create({
    message: 'Copied to clipboard',
    duration: 1500,
    position: 'bottom',
    color: 'dark'
  });
  await toast.present();
}

// PDF Download
async function downloadMinutesPDF() {
  if (!recording.value?.minutes) return;
  generatingPDF.value = true;
  try {
    const template = templates.value[selectedTemplate.value] || templates.value.professional;
    const blob = await generateMinutesPdf(
      recording.value.title,
      formatDate(recording.value.createdAt),
      recording.value.minutes,
      template,
      logoBase64.value
    );
    await downloadBlob(blob, `${recording.value.title}-minutes.pdf`);
  } catch (err) {
    console.error('PDF generation failed:', err);
    const toast = await toastController.create({ message: 'Failed to generate PDF', duration: 2000, color: 'danger', position: 'bottom' });
    await toast.present();
  } finally {
    generatingPDF.value = false;
  }
}

async function downloadSummaryPDF() {
  if (!recording.value?.summary) return;
  generatingPDF.value = true;
  try {
    const blob = await generateSummaryPdf(
      recording.value.title,
      formatDate(recording.value.createdAt),
      recording.value.summary
    );
    await downloadBlob(blob, `${recording.value.title}-summary.pdf`);
  } catch (err) {
    console.error('PDF generation failed:', err);
    const toast = await toastController.create({ message: 'Failed to generate PDF', duration: 2000, color: 'danger', position: 'bottom' });
    await toast.present();
  } finally {
    generatingPDF.value = false;
  }
}

async function downloadBlob(blob: Blob, filename: string) {
  // On Android/iOS (Capacitor WebView), use Web Share API with file —
  // this opens the native share sheet so the user can save to Downloads, Drive, etc.
  try {
    const file = new File([blob], filename, { type: 'application/pdf' });
    if (navigator.canShare?.({ files: [file] })) {
      await navigator.share({ files: [file], title: filename });
      return; // share sheet handled it
    }
  } catch (err: any) {
    if (err?.name === 'AbortError') return; // user dismissed share sheet — that's fine
    // For other errors fall through to the anchor fallback below
  }

  // Desktop browser fallback: programmatic anchor click
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);

  const toast = await toastController.create({
    message: 'PDF downloaded',
    duration: 1500,
    position: 'bottom',
    color: 'dark'
  });
  await toast.present();
}

// Template Management
function openTemplateEditor(key?: string) {
  editingTemplateKey.value = key || null;
  showTemplateEditor.value = true;
}

async function handleTemplateSave(key: string | null, template: PdfTemplate, logo: string | null, logoChanged: boolean) {
  if (key) {
    templates.value[key] = template;
    selectedTemplate.value = key;
  } else {
    const newKey = template.name.toLowerCase().replace(/\s+/g, '-') + '-' + Date.now();
    templates.value[newKey] = template;
    selectedTemplate.value = newKey;
  }
  await saveCustomTemplates(templates.value);

  if (logoChanged) {
    if (logo) {
      await saveLogo(logo);
    } else {
      await removeLogo();
    }
    logoBase64.value = logo;
  }

  showTemplateEditor.value = false;
}

async function handleTemplateDelete(key: string) {
  delete templates.value[key];
  if (selectedTemplate.value === key) {
    selectedTemplate.value = 'professional';
  }
  await saveCustomTemplates(templates.value);
  showTemplateEditor.value = false;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatDuration(seconds: number) {
  if (!seconds) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function formatStatus(status: string) {
  const map: Record<string, string> = {
    pending: 'Pending', transcribing: 'Processing', transcribed: 'Transcribed',
    summarized: 'Summarized', completed: 'Complete', failed: 'Failed'
  };
  return map[status] || status;
}

function renderMarkdown(text: string): string {
  if (!text) return '';

  // Escape HTML to prevent XSS
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Process line by line
  const lines = html.split('\n');
  const result: string[] = [];
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Headings
    const headingMatch = line.match(/^(#{1,4})\s+(.+)$/);
    if (headingMatch) {
      if (inList) { result.push('</ul>'); inList = false; }
      const level = headingMatch[1].length;
      const content = applyInlineFormatting(headingMatch[2]);
      result.push(`<h${level + 1}>${content}</h${level + 1}>`);
      continue;
    }

    // Bullet points (* or -)
    const bulletMatch = line.match(/^(\s*)[\*\-]\s+(.+)$/);
    if (bulletMatch) {
      if (!inList) { result.push('<ul>'); inList = true; }
      const content = applyInlineFormatting(bulletMatch[2]);
      result.push(`<li>${content}</li>`);
      continue;
    }

    // Close list if we hit a non-bullet line
    if (inList && line.trim() !== '') {
      result.push('</ul>');
      inList = false;
    }

    // Empty line
    if (line.trim() === '') {
      if (inList) { result.push('</ul>'); inList = false; }
      result.push('<br>');
      continue;
    }

    // Regular paragraph
    result.push(`<p>${applyInlineFormatting(line)}</p>`);
  }

  if (inList) result.push('</ul>');
  return result.join('');
}

function applyInlineFormatting(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>');
}
</script>

<style scoped>
.detail-page {
  padding: 20px 20px 40px;
}

/* Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.header-btn {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--app-border);
  background: var(--app-surface);
  color: var(--app-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-xs);
  transition: all var(--transition-fast);
}

.header-btn:active { transform: scale(0.93); }
.header-btn ion-icon { font-size: 22px; }

.header-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
}

/* Loading */
.loading-state { display: flex; justify-content: center; padding: 64px; }

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(245, 158, 11, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-icon-wrap ion-icon { font-size: 28px; color: var(--ion-color-warning); }
.empty-state h3 { font-size: 18px; font-weight: 700; color: var(--app-text); margin: 0 0 12px; }

.link-btn {
  background: none;
  border: none;
  color: var(--app-primary);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
}

/* Title Section */
.title-section {
  margin-bottom: 20px;
}

.title-section h1 {
  font-size: 24px;
  font-weight: 800;
  color: var(--app-text);
  margin: 0 0 12px;
  line-height: 1.3;
  letter-spacing: -0.3px;
}

.meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--radius-full);
  font-size: 12px;
  color: var(--app-text-secondary);
  font-weight: 500;
}

.meta-chip ion-icon {
  font-size: 14px;
  color: var(--app-text-muted);
}

.status-chip {
  padding: 5px 12px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 700;
}

.status-chip.pending { background: rgba(245, 158, 11, 0.1); color: var(--ion-color-warning); }
.status-chip.transcribed, .status-chip.summarized, .status-chip.completed { background: rgba(34, 197, 94, 0.1); color: var(--ion-color-success); }
.status-chip.failed { background: rgba(239, 68, 68, 0.1); color: var(--ion-color-danger); }

/* Player */
.player-section {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--radius-2xl);
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}

.player-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: var(--app-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  box-shadow: var(--shadow-primary);
  transition: transform var(--transition-fast);
}

.player-btn:active { transform: scale(0.93); }
.player-btn ion-icon { font-size: 22px; }

.player-body { flex: 1; }

.player-bar {
  position: relative;
  height: 6px;
  background: var(--app-border);
  border-radius: 3px;
  cursor: pointer;
  margin-bottom: 10px;
}

.bar-fill {
  height: 100%;
  background: var(--app-gradient);
  border-radius: 3px;
  transition: width 0.1s;
}

.bar-thumb {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--app-primary);
  border: 3px solid var(--app-surface);
  box-shadow: var(--shadow-sm);
  transform: translate(-50%, -50%);
  transition: left 0.1s;
}

.player-times {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--app-text-muted);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* AI Section */
.ai-section {
  margin-bottom: 24px;
}

.section-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--app-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin: 0 0 12px;
}

.ai-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.ai-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 18px 8px;
  background: var(--app-surface);
  border: 1.5px solid var(--app-border);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-xs);
}

.ai-card:active:not(:disabled) { transform: scale(0.96); }
.ai-card:disabled { opacity: 0.45; cursor: not-allowed; }

.ai-card.done {
  border-color: var(--app-primary);
  background: var(--app-primary-ultra-light);
}

.ai-card.active {
  border-color: var(--app-primary);
}

.ai-card-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--app-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-card-icon ion-icon { font-size: 22px; color: var(--app-primary); }
.ai-card-icon ion-spinner { width: 22px; height: 22px; color: var(--app-primary); }
.ai-card-icon.done { background: var(--app-gradient); }
.ai-card-icon.done ion-icon { color: white; }

.ai-card-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--app-text);
  text-align: center;
}

/* Content Tabs */
.content-section {
  margin-bottom: 20px;
}

.content-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
}

.content-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 8px;
  background: none;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.content-tab.active {
  background: var(--app-gradient);
  color: white;
  box-shadow: var(--shadow-primary);
}

.content-tab ion-icon { font-size: 16px; }

/* Tab Content */
.tab-content {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--radius-2xl);
  overflow: hidden;
  box-shadow: var(--shadow-xs);
}

.tab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid var(--app-border);
}

.tab-header h3 {
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
  margin: 0;
}

.tab-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--app-border);
  background: var(--app-bg);
  color: var(--app-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:active:not(:disabled) {
  transform: scale(0.93);
  background: var(--app-primary-ultra-light);
  color: var(--app-primary);
  border-color: var(--app-primary);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn ion-icon { font-size: 16px; }

/* Template Bar */
.template-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 18px;
  border-bottom: 1px solid var(--app-border);
  background: var(--app-bg);
}

.template-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.template-selector label {
  font-size: 12px;
  font-weight: 700;
  color: var(--app-text-muted);
  white-space: nowrap;
}

.template-select {
  flex: 1;
  min-width: 0;
  padding: 7px 10px;
  border: 1px solid var(--app-border);
  border-radius: var(--radius-md);
  background: var(--app-surface);
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text);
  -webkit-appearance: none;
  appearance: none;
}

.template-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.icon-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  border: 1px solid var(--app-border);
  background: var(--app-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-btn:active { transform: scale(0.93); }
.icon-btn ion-icon { font-size: 16px; }

.icon-btn.accent {
  color: var(--app-primary);
  border-color: var(--app-primary);
  background: var(--app-primary-ultra-light);
}

.tab-body {
  padding: 18px;
  font-size: 15px;
  line-height: 1.75;
  color: var(--app-text);
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

.tab-body.formatted {
  white-space: normal;
}

.tab-body.formatted h2 {
  font-size: 18px;
  font-weight: 700;
  color: var(--app-text);
  margin: 20px 0 8px;
}

.tab-body.formatted h2:first-child {
  margin-top: 0;
}

.tab-body.formatted h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text);
  margin: 16px 0 6px;
}

.tab-body.formatted h4 {
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text-secondary);
  margin: 12px 0 4px;
}

.tab-body.formatted h5 {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-secondary);
  margin: 10px 0 4px;
}

.tab-body.formatted p {
  margin: 4px 0;
}

.tab-body.formatted ul {
  margin: 6px 0;
  padding-left: 20px;
  list-style: none;
}

.tab-body.formatted ul li {
  position: relative;
  padding-left: 6px;
  margin: 4px 0;
}

.tab-body.formatted ul li::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 10px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--app-primary);
}

.tab-body.formatted strong {
  font-weight: 700;
  color: var(--app-text);
}

.tab-body.formatted em {
  font-style: italic;
  color: var(--app-text-secondary);
}

.tab-body.formatted code {
  font-family: monospace;
  font-size: 13px;
  background: var(--app-border);
  padding: 2px 6px;
  border-radius: 4px;
}

.tab-body.formatted br {
  display: block;
  content: '';
  margin: 4px 0;
}
</style>

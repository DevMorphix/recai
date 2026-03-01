<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="verify-page">
        <div class="bg-decoration">
          <div class="blob blob-1"></div>
          <div class="blob blob-2"></div>
        </div>

        <div class="verify-container">
          <!-- Icon -->
          <div class="icon-wrapper">
            <div class="icon-circle">
              <ion-icon :icon="mailOpenOutline"></ion-icon>
            </div>
            <div class="icon-glow"></div>
          </div>

          <h1>Check your email</h1>
          <p class="subtitle">We sent a 6-digit code to<br><strong>{{ email }}</strong></p>

          <!-- OTP Inputs -->
          <div class="otp-row">
            <input
              v-for="(_, i) in 6"
              :key="i"
              :ref="el => { if (el) inputs[i] = el as HTMLInputElement }"
              class="otp-input"
              type="text"
              inputmode="numeric"
              maxlength="1"
              :value="digits[i]"
              @input="onInput(i, $event)"
              @keydown="onKeydown(i, $event)"
              @paste="onPaste($event)"
            />
          </div>

          <div v-if="error" class="error-banner">
            <ion-icon :icon="alertCircleOutline"></ion-icon>
            <span>{{ error }}</span>
          </div>

          <button class="verify-btn" @click="handleVerify" :disabled="loading || otp.length < 6">
            <ion-spinner v-if="loading" name="crescent"></ion-spinner>
            <template v-else>
              <span>Verify Email</span>
              <ion-icon :icon="checkmarkCircleOutline"></ion-icon>
            </template>
          </button>

          <!-- Resend -->
          <div class="resend-row">
            <span class="resend-label">Didn't receive it?</span>
            <button class="resend-btn" @click="handleResend" :disabled="resendCooldown > 0 || resending">
              <span v-if="resendCooldown > 0">Resend in {{ resendCooldown }}s</span>
              <span v-else-if="resending">Sending...</span>
              <span v-else>Resend code</span>
            </button>
          </div>

          <div v-if="resendSuccess" class="success-msg">
            <ion-icon :icon="checkmarkCircleOutline"></ion-icon>
            <span>New code sent!</span>
          </div>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { IonPage, IonContent, IonIcon, IonSpinner } from '@ionic/vue';
import { mailOpenOutline, alertCircleOutline, checkmarkCircleOutline } from 'ionicons/icons';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const email = ref((route.query.email as string) || '');
const digits = ref<string[]>(Array(6).fill(''));
const inputs = ref<HTMLInputElement[]>([]);
const loading = ref(false);
const error = ref('');
const resending = ref(false);
const resendCooldown = ref(0);
const resendSuccess = ref(false);

let cooldownTimer: ReturnType<typeof setInterval> | null = null;

const otp = computed(() => digits.value.join(''));

onMounted(() => {
  setTimeout(() => inputs.value[0]?.focus(), 300);
});

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer);
});

function onInput(index: number, event: Event) {
  const val = (event.target as HTMLInputElement).value.replace(/\D/g, '').slice(-1);
  digits.value[index] = val;
  (event.target as HTMLInputElement).value = val;
  if (val && index < 5) {
    inputs.value[index + 1]?.focus();
  }
  error.value = '';
}

function onKeydown(index: number, event: KeyboardEvent) {
  if (event.key === 'Backspace' && !digits.value[index] && index > 0) {
    digits.value[index - 1] = '';
    inputs.value[index - 1]?.focus();
  }
}

function onPaste(event: ClipboardEvent) {
  event.preventDefault();
  const text = event.clipboardData?.getData('text') || '';
  const nums = text.replace(/\D/g, '').slice(0, 6).split('');
  nums.forEach((n, i) => { digits.value[i] = n; });
  const nextEmpty = Math.min(nums.length, 5);
  inputs.value[nextEmpty]?.focus();
}

async function handleVerify() {
  if (otp.value.length < 6) return;
  loading.value = true;
  error.value = '';
  const success = await auth.verifyEmail(email.value, otp.value);
  loading.value = false;
  if (success) {
    router.replace('/home');
  } else {
    error.value = auth.error || 'Invalid code';
    digits.value = Array(6).fill('');
    setTimeout(() => inputs.value[0]?.focus(), 100);
  }
}

async function handleResend() {
  resending.value = true;
  resendSuccess.value = false;
  const ok = await auth.sendVerification(email.value);
  resending.value = false;
  if (ok) {
    resendSuccess.value = true;
    resendCooldown.value = 60;
    cooldownTimer = setInterval(() => {
      resendCooldown.value--;
      if (resendCooldown.value <= 0) {
        clearInterval(cooldownTimer!);
        resendSuccess.value = false;
      }
    }, 1000);
  } else {
    error.value = auth.error || 'Failed to resend';
  }
}
</script>

<style scoped>
.verify-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--app-bg);
  position: relative;
  overflow: hidden;
}

.bg-decoration { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
.blob { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.35; animation: float 20s ease-in-out infinite; }
.blob-1 { width: 280px; height: 280px; background: rgba(5,150,105,0.2); top: -80px; right: -60px; }
.blob-2 { width: 220px; height: 220px; background: rgba(16,185,129,0.15); bottom: -40px; left: -40px; animation-delay: -10s; }

@keyframes float {
  0%,100% { transform: translate(0,0) scale(1); }
  25% { transform: translate(20px,-15px) scale(1.03); }
  50% { transform: translate(-15px,15px) scale(0.97); }
  75% { transform: translate(10px,8px) scale(1.01); }
}

.verify-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 380px;
  padding: 32px 24px;
  text-align: center;
}

.icon-wrapper {
  position: relative;
  display: inline-flex;
  margin-bottom: 28px;
}

.icon-circle {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  background: var(--app-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
  box-shadow: var(--shadow-primary-lg);
}

.icon-circle ion-icon { font-size: 36px; color: white; }

.icon-glow {
  position: absolute;
  inset: -8px;
  border-radius: 28px;
  background: var(--app-gradient);
  opacity: 0.2;
  filter: blur(16px);
}

h1 {
  font-size: 28px;
  font-weight: 800;
  color: var(--app-text);
  margin: 0 0 10px;
  letter-spacing: -0.3px;
}

.subtitle {
  font-size: 15px;
  color: var(--app-text-muted);
  margin: 0 0 32px;
  line-height: 1.5;
}

.subtitle strong { color: var(--app-text-secondary); }

/* OTP row */
.otp-row {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 24px;
}

.otp-input {
  width: 48px;
  height: 56px;
  border-radius: var(--radius-lg);
  border: 2px solid var(--app-border);
  background: var(--app-surface);
  font-size: 22px;
  font-weight: 700;
  color: var(--app-text);
  text-align: center;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  caret-color: var(--app-primary);
}

.otp-input:focus {
  border-color: var(--app-primary);
  box-shadow: 0 0 0 4px var(--app-primary-ultra-light);
}

/* Error */
.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.15);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  animation: shake 0.4s ease-in-out;
}
.error-banner ion-icon { font-size: 18px; color: var(--ion-color-danger); flex-shrink: 0; }
.error-banner span { font-size: 13px; color: var(--ion-color-danger); font-weight: 500; }

@keyframes shake {
  0%,100% { transform: translateX(0); }
  20% { transform: translateX(-5px); }
  40% { transform: translateX(5px); }
  60% { transform: translateX(-3px); }
  80% { transform: translateX(3px); }
}

/* Verify button */
.verify-btn {
  width: 100%;
  height: 54px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--app-gradient);
  color: white;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: var(--shadow-primary);
  transition: all var(--transition-base);
  margin-bottom: 20px;
}
.verify-btn:active:not(:disabled) { transform: scale(0.98); }
.verify-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.verify-btn ion-icon { font-size: 20px; }
.verify-btn ion-spinner { width: 22px; height: 22px; color: white; }

/* Resend */
.resend-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.resend-label { font-size: 14px; color: var(--app-text-muted); }
.resend-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--app-primary);
  cursor: pointer;
}
.resend-btn:disabled { opacity: 0.5; cursor: not-allowed; color: var(--app-text-muted); }

.success-msg {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 12px;
  color: var(--ion-color-success);
  font-size: 13px;
  font-weight: 600;
}
.success-msg ion-icon { font-size: 16px; }
</style>

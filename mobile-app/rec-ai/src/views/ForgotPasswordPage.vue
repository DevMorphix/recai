<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="fp-page">
        <div class="bg-decoration">
          <div class="blob blob-1"></div>
          <div class="blob blob-2"></div>
        </div>

        <div class="fp-container">
          <button class="back-btn" @click="step > 1 ? step-- : router.back()">
            <ion-icon :icon="arrowBackOutline"></ion-icon>
          </button>

          <!-- Step indicator -->
          <div class="steps">
            <div class="step" :class="{ active: step >= 1, done: step > 1 }">1</div>
            <div class="step-line" :class="{ active: step > 1 }"></div>
            <div class="step" :class="{ active: step >= 2, done: step > 2 }">2</div>
            <div class="step-line" :class="{ active: step > 2 }"></div>
            <div class="step" :class="{ active: step >= 3 }">3</div>
          </div>

          <!-- STEP 1: Enter email -->
          <div v-if="step === 1">
            <h1>Forgot password?</h1>
            <p class="subtitle">Enter your email and we'll send you a reset code</p>

            <div class="form-card">
              <div class="input-field" :class="{ focused: emailFocused }">
                <ion-icon :icon="mailOutline" class="field-icon"></ion-icon>
                <input
                  v-model="email"
                  type="email"
                  placeholder="your@email.com"
                  @focus="emailFocused = true"
                  @blur="emailFocused = false"
                  @keyup.enter="handleSendCode"
                  :disabled="auth.loading"
                  autocomplete="email"
                />
              </div>

              <div v-if="error" class="error-banner">
                <ion-icon :icon="alertCircleOutline"></ion-icon>
                <span>{{ error }}</span>
              </div>

              <button class="action-btn" @click="handleSendCode" :disabled="auth.loading || !email">
                <ion-spinner v-if="auth.loading" name="crescent"></ion-spinner>
                <template v-else>
                  <span>Send Reset Code</span>
                  <ion-icon :icon="arrowForwardOutline"></ion-icon>
                </template>
              </button>
            </div>
          </div>

          <!-- STEP 2: Enter OTP -->
          <div v-if="step === 2">
            <h1>Enter the code</h1>
            <p class="subtitle">We sent a 6-digit code to<br><strong>{{ email }}</strong></p>

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

            <button class="action-btn" @click="handleVerifyOtp" :disabled="otp.length < 6">
              <span>Continue</span>
              <ion-icon :icon="arrowForwardOutline"></ion-icon>
            </button>

            <div class="resend-row">
              <span class="resend-label">Didn't get it?</span>
              <button class="resend-btn" @click="handleSendCode" :disabled="resendCooldown > 0 || auth.loading">
                <span v-if="resendCooldown > 0">Resend in {{ resendCooldown }}s</span>
                <span v-else>Resend</span>
              </button>
            </div>
          </div>

          <!-- STEP 3: New password -->
          <div v-if="step === 3">
            <h1>New password</h1>
            <p class="subtitle">Choose a strong password for your account</p>

            <div class="form-card">
              <div class="input-wrapper">
                <div class="input-field" :class="{ focused: pwFocused }">
                  <ion-icon :icon="lockClosedOutline" class="field-icon"></ion-icon>
                  <input
                    v-model="newPassword"
                    :type="showPw ? 'text' : 'password'"
                    placeholder="New password (min 6 chars)"
                    @focus="pwFocused = true"
                    @blur="pwFocused = false"
                    :disabled="auth.loading"
                  />
                  <button type="button" class="toggle-pw" @click="showPw = !showPw">
                    <ion-icon :icon="showPw ? eyeOffOutline : eyeOutline"></ion-icon>
                  </button>
                </div>
              </div>

              <div class="input-wrapper">
                <div class="input-field" :class="{ focused: confirmFocused, success: confirmPassword && newPassword === confirmPassword }">
                  <ion-icon :icon="shieldCheckmarkOutline" class="field-icon"></ion-icon>
                  <input
                    v-model="confirmPassword"
                    :type="showPw ? 'text' : 'password'"
                    placeholder="Confirm password"
                    @focus="confirmFocused = true"
                    @blur="confirmFocused = false"
                    :disabled="auth.loading"
                  />
                </div>
              </div>

              <div v-if="error" class="error-banner">
                <ion-icon :icon="alertCircleOutline"></ion-icon>
                <span>{{ error }}</span>
              </div>

              <button class="action-btn" @click="handleReset" :disabled="auth.loading || !newPassword || !confirmPassword">
                <ion-spinner v-if="auth.loading" name="crescent"></ion-spinner>
                <template v-else>
                  <span>Reset Password</span>
                  <ion-icon :icon="checkmarkCircleOutline"></ion-icon>
                </template>
              </button>
            </div>
          </div>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { IonPage, IonContent, IonIcon, IonSpinner } from '@ionic/vue';
import {
  arrowBackOutline, arrowForwardOutline, mailOutline, lockClosedOutline,
  eyeOutline, eyeOffOutline, shieldCheckmarkOutline, alertCircleOutline, checkmarkCircleOutline
} from 'ionicons/icons';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const auth = useAuthStore();

const step = ref(1);
const email = ref('');
const emailFocused = ref(false);
const error = ref('');

// OTP step
const digits = ref<string[]>(Array(6).fill(''));
const inputs = ref<HTMLInputElement[]>([]);
const resendCooldown = ref(0);
let cooldownTimer: ReturnType<typeof setInterval> | null = null;

// Password step
const newPassword = ref('');
const confirmPassword = ref('');
const showPw = ref(false);
const pwFocused = ref(false);
const confirmFocused = ref(false);

onUnmounted(() => { if (cooldownTimer) clearInterval(cooldownTimer); });

const otp = computed(() => digits.value.join(''));

watch(step, (s) => {
  if (s === 2) {
    digits.value = Array(6).fill('');
    setTimeout(() => inputs.value[0]?.focus(), 300);
  }
  error.value = '';
});

async function handleSendCode() {
  if (!email.value) return;
  error.value = '';
  const ok = await auth.forgotPassword(email.value);
  if (ok) {
    step.value = 2;
    startCooldown();
  } else {
    // Always show step 2 (prevents email enumeration on UI too)
    step.value = 2;
    startCooldown();
  }
}

function startCooldown() {
  resendCooldown.value = 60;
  if (cooldownTimer) clearInterval(cooldownTimer);
  cooldownTimer = setInterval(() => {
    resendCooldown.value--;
    if (resendCooldown.value <= 0) clearInterval(cooldownTimer!);
  }, 1000);
}

function onInput(index: number, event: Event) {
  const val = (event.target as HTMLInputElement).value.replace(/\D/g, '').slice(-1);
  digits.value[index] = val;
  (event.target as HTMLInputElement).value = val;
  if (val && index < 5) inputs.value[index + 1]?.focus();
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
  const nums = (event.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6).split('');
  nums.forEach((n, i) => { digits.value[i] = n; });
  inputs.value[Math.min(nums.length, 5)]?.focus();
}

function handleVerifyOtp() {
  if (otp.value.length < 6) return;
  error.value = '';
  step.value = 3;
}

async function handleReset() {
  error.value = '';
  if (newPassword.value.length < 6) {
    error.value = 'Password must be at least 6 characters';
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match';
    return;
  }
  const ok = await auth.resetPassword(email.value, otp.value, newPassword.value);
  if (ok) {
    router.replace('/login');
  } else {
    error.value = auth.error || 'Reset failed. The code may have expired.';
    // Go back to OTP step to retry
    step.value = 2;
    digits.value = Array(6).fill('');
  }
}
</script>

<style scoped>
.fp-page {
  min-height: 100%;
  background: var(--app-bg);
  position: relative;
  overflow: hidden;
}

.bg-decoration { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
.blob { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.35; animation: float 20s ease-in-out infinite; }
.blob-1 { width: 280px; height: 280px; background: rgba(5,150,105,0.18); top: -80px; left: -60px; }
.blob-2 { width: 220px; height: 220px; background: rgba(16,185,129,0.14); bottom: -40px; right: -40px; animation-delay: -10s; }

@keyframes float {
  0%,100% { transform: translate(0,0) scale(1); }
  25% { transform: translate(20px,-15px) scale(1.03); }
  50% { transform: translate(-15px,15px) scale(0.97); }
  75% { transform: translate(10px,8px) scale(1.01); }
}

.fp-container {
  position: relative;
  z-index: 1;
  max-width: 400px;
  margin: 0 auto;
  padding: calc(20px + env(safe-area-inset-top, 0px)) 24px 40px;
}

.back-btn {
  width: 44px; height: 44px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--app-border);
  background: var(--app-surface);
  color: var(--app-text);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; margin-bottom: 24px;
  box-shadow: var(--shadow-xs);
}
.back-btn ion-icon { font-size: 22px; }

/* Steps indicator */
.steps {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 32px;
}
.step {
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 2px solid var(--app-border);
  background: var(--app-surface);
  color: var(--app-text-muted);
  font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.3s;
  flex-shrink: 0;
}
.step.active { border-color: var(--app-primary); background: var(--app-primary); color: white; }
.step.done { border-color: var(--app-primary); background: var(--app-primary); color: white; }
.step-line { flex: 1; height: 2px; background: var(--app-border); transition: background 0.3s; }
.step-line.active { background: var(--app-primary); }

h1 {
  font-size: 28px; font-weight: 800;
  color: var(--app-text); margin: 0 0 8px;
  letter-spacing: -0.3px;
}
.subtitle {
  font-size: 15px; color: var(--app-text-muted);
  margin: 0 0 28px; line-height: 1.5;
}
.subtitle strong { color: var(--app-text-secondary); }

/* Form card */
.form-card {
  background: var(--app-surface);
  border-radius: var(--radius-2xl);
  padding: 24px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--app-border);
}

.input-wrapper { margin-bottom: 14px; }

.input-field {
  display: flex; align-items: center; gap: 12px;
  padding: 0 16px; height: 52px;
  background: var(--app-bg);
  border: 2px solid transparent;
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}
.input-field.focused {
  border-color: var(--app-primary);
  background: var(--app-surface);
  box-shadow: 0 0 0 4px var(--app-primary-ultra-light);
}
.input-field.success { border-color: var(--ion-color-success); }
.field-icon { font-size: 18px; color: var(--app-text-muted); flex-shrink: 0; }
.input-field.focused .field-icon { color: var(--app-primary); }
.input-field input { flex: 1; border: none; background: none; font-size: 15px; color: var(--app-text); outline: none; min-width: 0; }
.input-field input::placeholder { color: var(--app-text-muted); }
.toggle-pw { background: none; border: none; padding: 4px; cursor: pointer; display: flex; color: var(--app-text-muted); }
.toggle-pw ion-icon { font-size: 18px; }

/* OTP row */
.otp-row { display: flex; gap: 10px; justify-content: center; margin-bottom: 24px; }
.otp-input {
  width: 48px; height: 56px;
  border-radius: var(--radius-lg);
  border: 2px solid var(--app-border);
  background: var(--app-surface);
  font-size: 22px; font-weight: 700;
  color: var(--app-text); text-align: center; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.otp-input:focus { border-color: var(--app-primary); box-shadow: 0 0 0 4px var(--app-primary-ultra-light); }

/* Error */
.error-banner {
  display: flex; align-items: center; gap: 8px;
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

/* Action button */
.action-btn {
  width: 100%; height: 54px;
  border: none; border-radius: var(--radius-lg);
  background: var(--app-gradient);
  color: white; font-size: 16px; font-weight: 700;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px;
  box-shadow: var(--shadow-primary);
  transition: all var(--transition-base);
  margin-top: 4px;
}
.action-btn:active:not(:disabled) { transform: scale(0.98); }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.action-btn ion-icon { font-size: 20px; }
.action-btn ion-spinner { width: 22px; height: 22px; color: white; }

/* Resend */
.resend-row { display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: 16px; }
.resend-label { font-size: 14px; color: var(--app-text-muted); }
.resend-btn { background: none; border: none; padding: 0; font-size: 14px; font-weight: 700; color: var(--app-primary); cursor: pointer; }
.resend-btn:disabled { opacity: 0.5; cursor: not-allowed; color: var(--app-text-muted); }
</style>

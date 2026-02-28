<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="register-page">
        <!-- Animated Background -->
        <div class="bg-decoration">
          <div class="blob blob-1"></div>
          <div class="blob blob-2"></div>
        </div>

        <div class="register-container">
          <!-- Back Button -->
          <button class="back-btn" @click="router.back()">
            <ion-icon :icon="arrowBackOutline"></ion-icon>
          </button>

          <!-- Header -->
          <div class="header-section">
            <h1>Create Account</h1>
            <p>Join RecAI and unlock the power of voice</p>
          </div>

          <!-- Form Card -->
          <div class="form-card">
            <form @submit.prevent="handleRegister">
              <div class="input-wrapper">
                <label>Full Name</label>
                <div class="input-field" :class="{ focused: nameFocused }">
                  <ion-icon :icon="personOutline" class="field-icon"></ion-icon>
                  <input
                    v-model="name"
                    type="text"
                    placeholder="John Doe"
                    :disabled="loading"
                    @focus="nameFocused = true"
                    @blur="nameFocused = false"
                    autocomplete="name"
                  />
                </div>
              </div>

              <div class="input-wrapper">
                <label>Email</label>
                <div class="input-field" :class="{ focused: emailFocused }">
                  <ion-icon :icon="mailOutline" class="field-icon"></ion-icon>
                  <input
                    v-model="email"
                    type="email"
                    placeholder="you@example.com"
                    :disabled="loading"
                    @focus="emailFocused = true"
                    @blur="emailFocused = false"
                    autocomplete="email"
                  />
                </div>
              </div>

              <div class="input-wrapper">
                <label>Password</label>
                <div class="input-field" :class="{ focused: passwordFocused }">
                  <ion-icon :icon="lockClosedOutline" class="field-icon"></ion-icon>
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="Min 6 characters"
                    :disabled="loading"
                    @focus="passwordFocused = true"
                    @blur="passwordFocused = false"
                    autocomplete="new-password"
                  />
                  <button type="button" class="toggle-pw" @click="showPassword = !showPassword" tabindex="-1">
                    <ion-icon :icon="showPassword ? eyeOffOutline : eyeOutline"></ion-icon>
                  </button>
                </div>
                <!-- Password strength indicator -->
                <div class="pw-strength" v-if="password">
                  <div class="strength-bar">
                    <div class="strength-fill" :style="{ width: passwordStrength + '%' }" :class="strengthClass"></div>
                  </div>
                  <span :class="strengthClass">{{ strengthLabel }}</span>
                </div>
              </div>

              <div class="input-wrapper">
                <label>Confirm Password</label>
                <div class="input-field" :class="{ focused: confirmFocused, success: confirmPassword && password === confirmPassword }">
                  <ion-icon :icon="shieldCheckmarkOutline" class="field-icon"></ion-icon>
                  <input
                    v-model="confirmPassword"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="Re-enter password"
                    :disabled="loading"
                    @focus="confirmFocused = true"
                    @blur="confirmFocused = false"
                    autocomplete="new-password"
                  />
                  <ion-icon v-if="confirmPassword && password === confirmPassword" :icon="checkmarkCircleOutline" class="match-icon"></ion-icon>
                </div>
              </div>

              <div v-if="error" class="error-banner">
                <ion-icon :icon="alertCircleOutline"></ion-icon>
                <span>{{ error }}</span>
              </div>

              <button type="submit" class="submit-btn" :disabled="loading">
                <ion-spinner v-if="loading" name="crescent"></ion-spinner>
                <template v-else>
                  <span>Create Account</span>
                  <ion-icon :icon="arrowForwardOutline"></ion-icon>
                </template>
              </button>
            </form>
          </div>

          <!-- Footer -->
          <p class="login-link">
            Already have an account?
            <router-link to="/login">Sign in</router-link>
          </p>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { IonPage, IonContent, IonIcon, IonSpinner } from '@ionic/vue';
import {
  arrowBackOutline, personOutline, mailOutline, lockClosedOutline,
  eyeOutline, eyeOffOutline, shieldCheckmarkOutline, checkmarkCircleOutline,
  alertCircleOutline, arrowForwardOutline
} from 'ionicons/icons';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const auth = useAuthStore();

const name = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const showPassword = ref(false);
const loading = ref(false);
const error = ref('');
const nameFocused = ref(false);
const emailFocused = ref(false);
const passwordFocused = ref(false);
const confirmFocused = ref(false);

const passwordStrength = computed(() => {
  const p = password.value;
  if (!p) return 0;
  let score = 0;
  if (p.length >= 6) score += 25;
  if (p.length >= 8) score += 15;
  if (/[A-Z]/.test(p)) score += 20;
  if (/[0-9]/.test(p)) score += 20;
  if (/[^A-Za-z0-9]/.test(p)) score += 20;
  return Math.min(100, score);
});

const strengthClass = computed(() => {
  if (passwordStrength.value < 40) return 'weak';
  if (passwordStrength.value < 70) return 'medium';
  return 'strong';
});

const strengthLabel = computed(() => {
  if (passwordStrength.value < 40) return 'Weak';
  if (passwordStrength.value < 70) return 'Medium';
  return 'Strong';
});

async function handleRegister() {
  if (!name.value || !email.value || !password.value || !confirmPassword.value) {
    error.value = 'Please fill in all fields';
    return;
  }

  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match';
    return;
  }

  if (password.value.length < 6) {
    error.value = 'Password must be at least 6 characters';
    return;
  }

  loading.value = true;
  error.value = '';

  const success = await auth.register(name.value, email.value, password.value);

  if (success) {
    router.replace('/home');
  } else {
    error.value = auth.error || 'Registration failed';
  }

  loading.value = false;
}
</script>

<style scoped>
.register-page {
  min-height: 100%;
  background: var(--app-bg);
  position: relative;
  overflow: hidden;
}

.bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: float 20s ease-in-out infinite;
}

.blob-1 {
  width: 280px;
  height: 280px;
  background: rgba(5, 150, 105, 0.18);
  top: -80px;
  left: -60px;
}

.blob-2 {
  width: 220px;
  height: 220px;
  background: rgba(16, 185, 129, 0.14);
  bottom: -40px;
  right: -40px;
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(20px, -15px) scale(1.03); }
  50% { transform: translate(-15px, 15px) scale(0.97); }
  75% { transform: translate(10px, 8px) scale(1.01); }
}

.register-container {
  position: relative;
  z-index: 1;
  max-width: 400px;
  margin: 0 auto;
  padding: 20px 24px 40px;
}

/* Back Button */
.back-btn {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--app-border);
  background: var(--app-surface);
  color: var(--app-text);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-bottom: 24px;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-xs);
}

.back-btn:active {
  transform: scale(0.95);
}

.back-btn ion-icon {
  font-size: 22px;
}

/* Header */
.header-section {
  margin-bottom: 28px;
}

.header-section h1 {
  font-size: 30px;
  font-weight: 800;
  color: var(--app-text);
  margin: 0 0 8px;
  letter-spacing: -0.3px;
}

.header-section p {
  font-size: 15px;
  color: var(--app-text-muted);
  margin: 0;
}

/* Form Card */
.form-card {
  background: var(--app-surface);
  border-radius: var(--radius-2xl);
  padding: 28px 24px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--app-border);
}

.input-wrapper {
  margin-bottom: 18px;
}

.input-wrapper label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-field {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  height: 52px;
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

.input-field.success {
  border-color: var(--ion-color-success);
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.08);
}

.field-icon {
  font-size: 20px;
  color: var(--app-text-muted);
  flex-shrink: 0;
  transition: color var(--transition-fast);
}

.input-field.focused .field-icon {
  color: var(--app-primary);
}

.input-field.success .field-icon {
  color: var(--ion-color-success);
}

.input-field input {
  flex: 1;
  border: none;
  background: none;
  font-size: 15px;
  color: var(--app-text);
  outline: none;
  min-width: 0;
}

.input-field input::placeholder {
  color: var(--app-text-muted);
}

.toggle-pw {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  display: flex;
  color: var(--app-text-muted);
}

.toggle-pw ion-icon {
  font-size: 20px;
}

.match-icon {
  font-size: 20px;
  color: var(--ion-color-success);
  flex-shrink: 0;
}

/* Password Strength */
.pw-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: var(--app-border);
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  border-radius: 2px;
  transition: width var(--transition-base), background var(--transition-base);
}

.strength-fill.weak { background: var(--ion-color-danger); }
.strength-fill.medium { background: var(--ion-color-warning); }
.strength-fill.strong { background: var(--ion-color-success); }

.pw-strength span {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

span.weak { color: var(--ion-color-danger); }
span.medium { color: var(--ion-color-warning); }
span.strong { color: var(--ion-color-success); }

/* Error Banner */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: var(--radius-md);
  margin-bottom: 18px;
  animation: shake 0.4s ease-in-out;
}

.error-banner ion-icon {
  font-size: 20px;
  color: var(--ion-color-danger);
  flex-shrink: 0;
}

.error-banner span {
  font-size: 14px;
  color: var(--ion-color-danger);
  font-weight: 500;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}

/* Submit Button */
.submit-btn {
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
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.submit-btn ion-icon {
  font-size: 20px;
}

.submit-btn ion-spinner {
  width: 22px;
  height: 22px;
  color: white;
}

/* Login Link */
.login-link {
  text-align: center;
  margin-top: 24px;
  color: var(--app-text-muted);
  font-size: 15px;
}

.login-link a {
  color: var(--app-primary);
  text-decoration: none;
  font-weight: 700;
}
</style>

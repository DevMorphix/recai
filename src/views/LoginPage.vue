<template>
  <ion-page>
    <ion-content :fullscreen="true" :scroll-y="false">
      <div class="login-page">
        <!-- Animated Background -->
        <div class="bg-decoration">
          <div class="blob blob-1"></div>
          <div class="blob blob-2"></div>
          <div class="blob blob-3"></div>
        </div>

        <div class="login-container">
          <!-- Logo Section -->
          <div class="logo-section">
            <div class="logo-wrapper">
              <div class="logo">
                <ion-icon :icon="micOutline"></ion-icon>
              </div>
              <div class="logo-glow"></div>
            </div>
            <h1>RecAI</h1>
            <p class="tagline">Record. Transcribe. Understand.</p>
          </div>

          <!-- Form Card -->
          <div class="form-card">
            <form @submit.prevent="handleLogin">
              <div class="input-wrapper">
                <label>Email</label>
                <div class="input-field" :class="{ focused: emailFocused, error: error && !email }">
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
                <div class="input-field" :class="{ focused: passwordFocused, error: error && !password }">
                  <ion-icon :icon="lockClosedOutline" class="field-icon"></ion-icon>
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="Enter your password"
                    :disabled="loading"
                    @focus="passwordFocused = true"
                    @blur="passwordFocused = false"
                    autocomplete="current-password"
                  />
                  <button type="button" class="toggle-pw" @click="showPassword = !showPassword" tabindex="-1">
                    <ion-icon :icon="showPassword ? eyeOffOutline : eyeOutline"></ion-icon>
                  </button>
                </div>
              </div>

              <div v-if="error" class="error-banner">
                <ion-icon :icon="alertCircleOutline"></ion-icon>
                <span>{{ error }}</span>
              </div>

              <button type="submit" class="submit-btn" :disabled="loading">
                <ion-spinner v-if="loading" name="crescent"></ion-spinner>
                <template v-else>
                  <span>Sign In</span>
                  <ion-icon :icon="arrowForwardOutline"></ion-icon>
                </template>
              </button>
            </form>
          </div>

          <!-- Footer -->
          <p class="register-link">
            Don't have an account?
            <router-link to="/register">Create one</router-link>
          </p>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { IonPage, IonContent, IonIcon, IonSpinner } from '@ionic/vue';
import { micOutline, mailOutline, lockClosedOutline, eyeOutline, eyeOffOutline, alertCircleOutline, arrowForwardOutline } from 'ionicons/icons';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const auth = useAuthStore();

const email = ref('');
const password = ref('');
const showPassword = ref(false);
const loading = ref(false);
const error = ref('');
const emailFocused = ref(false);
const passwordFocused = ref(false);

async function handleLogin() {
  if (!email.value || !password.value) {
    error.value = 'Please fill in all fields';
    return;
  }

  loading.value = true;
  error.value = '';

  const success = await auth.login(email.value, password.value);

  if (success) {
    router.replace('/home');
  } else {
    error.value = auth.error || 'Login failed';
  }

  loading.value = false;
}
</script>

<style scoped>
.login-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--app-bg);
  position: relative;
  overflow: hidden;
}

/* Animated Background Blobs */
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
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.blob-1 {
  width: 300px;
  height: 300px;
  background: rgba(5, 150, 105, 0.2);
  top: -100px;
  right: -80px;
  animation-delay: 0s;
}

.blob-2 {
  width: 250px;
  height: 250px;
  background: rgba(16, 185, 129, 0.15);
  bottom: -60px;
  left: -60px;
  animation-delay: -7s;
}

.blob-3 {
  width: 200px;
  height: 200px;
  background: rgba(52, 211, 153, 0.12);
  top: 40%;
  left: 50%;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -20px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(15px, 10px) scale(1.02); }
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 24px;
}

/* Logo */
.logo-section {
  text-align: center;
  margin-bottom: 40px;
}

.logo-wrapper {
  position: relative;
  display: inline-flex;
  margin-bottom: 20px;
}

.logo {
  width: 88px;
  height: 88px;
  border-radius: 28px;
  background: var(--app-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
  box-shadow: var(--shadow-primary-lg);
}

.logo ion-icon {
  font-size: 42px;
  color: white;
}

.logo-glow {
  position: absolute;
  inset: -8px;
  border-radius: 32px;
  background: var(--app-gradient);
  opacity: 0.2;
  filter: blur(16px);
  animation: glow-pulse 3s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(1.05); }
}

.logo-section h1 {
  font-size: 36px;
  font-weight: 800;
  color: var(--app-text);
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.tagline {
  font-size: 15px;
  color: var(--app-text-muted);
  margin: 0;
  letter-spacing: 0.3px;
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
  margin-bottom: 20px;
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

.input-field.error {
  border-color: var(--ion-color-danger);
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.08);
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
  transition: color var(--transition-fast);
}

.toggle-pw:hover {
  color: var(--app-text-secondary);
}

.toggle-pw ion-icon {
  font-size: 20px;
}

/* Error Banner */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: var(--radius-md);
  margin-bottom: 20px;
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
  position: relative;
  overflow: hidden;
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
  box-shadow: var(--shadow-sm);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.submit-btn ion-icon {
  font-size: 20px;
  transition: transform var(--transition-fast);
}

.submit-btn:hover:not(:disabled) ion-icon {
  transform: translateX(3px);
}

.submit-btn ion-spinner {
  width: 22px;
  height: 22px;
  color: white;
}

/* Register Link */
.register-link {
  text-align: center;
  margin-top: 28px;
  color: var(--app-text-muted);
  font-size: 15px;
}

.register-link a {
  color: var(--app-primary);
  text-decoration: none;
  font-weight: 700;
  transition: opacity var(--transition-fast);
}

.register-link a:hover {
  opacity: 0.8;
}
</style>

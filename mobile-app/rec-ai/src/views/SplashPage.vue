<template>
  <ion-page>
    <ion-content :fullscreen="true" :scroll-y="false">
      <div class="splash-page" :class="{ 'fade-out': leaving }">
        <!-- Animated Background -->
        <div class="bg-decoration">
          <div class="blob blob-1"></div>
          <div class="blob blob-2"></div>
          <div class="blob blob-3"></div>
        </div>

        <!-- Center Content -->
        <div class="splash-content">
          <!-- Logo -->
          <div class="logo-wrapper">
            <div class="logo">
              <img src="/logo.png" alt="App Logo" style="width: 82px; height: 82px; object-fit: contain;" />
            </div>
            <div class="logo-glow"></div>
            <div class="logo-ring"></div>
          </div>

          <!-- Title -->
          <h1 class="title">Echobit</h1>

          <!-- Tagline -->
          <div class="tagline">
            <span class="word word-1">Record.</span>
            <span class="word word-2">Transcribe.</span>
            <span class="word word-3">Understand.</span>
          </div>
        </div>

        <!-- Bottom shimmer bar -->
        <div class="bottom-section">
          <div class="shimmer-bar">
            <div class="shimmer-fill"></div>
          </div>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { IonPage, IonContent, IonIcon } from '@ionic/vue';
import { micOutline } from 'ionicons/icons';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const auth = useAuthStore();
const leaving = ref(false);

onMounted(async () => {
  // Initialize auth while animation plays
  const authReady = auth.initialize();

  // Wait for both the animation duration and auth to complete
  const [_] = await Promise.all([
    authReady,
    new Promise(resolve => setTimeout(resolve, 2500))
  ]);

  // Fade out
  leaving.value = true;

  // Navigate after fade-out animation
  setTimeout(() => {
    const target = auth.isAuthenticated ? '/home' : '/login';
    router.replace(target);
  }, 500);
});
</script>

<style scoped>
.splash-page {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--app-bg);
  padding-top: env(safe-area-inset-top, 0px);
  position: relative;
  overflow: hidden;
  transition: opacity 500ms ease-out;
}

.splash-page.fade-out {
  opacity: 0;
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
  opacity: 0;
  animation: blob-appear 1s ease-out forwards, float 20s ease-in-out infinite;
}

.blob-1 {
  width: 350px;
  height: 350px;
  background: rgba(5, 150, 105, 0.25);
  top: -120px;
  right: -100px;
  animation-delay: 0s, 0s;
}

.blob-2 {
  width: 280px;
  height: 280px;
  background: rgba(16, 185, 129, 0.2);
  bottom: -80px;
  left: -80px;
  animation-delay: 0.3s, -7s;
}

.blob-3 {
  width: 220px;
  height: 220px;
  background: rgba(52, 211, 153, 0.15);
  top: 35%;
  left: 55%;
  animation-delay: 0.6s, -14s;
}

@keyframes blob-appear {
  from { opacity: 0; transform: scale(0.5); }
  to { opacity: 0.5; transform: scale(1); }
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -20px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(15px, 10px) scale(1.02); }
}

/* Center Content */
.splash-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

/* Logo */
.logo-wrapper {
  position: relative;
  display: inline-flex;
  animation: logo-enter 800ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  opacity: 0;
  transform: scale(0.3);
}

@keyframes logo-enter {
  from {
    opacity: 0;
    transform: scale(0.3) rotate(-10deg);
  }
  to {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

.logo {
  width: 110px;
  height: 110px;
  border-radius: 32px;
  background: var(--app-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 2;
  box-shadow: var(--shadow-primary-lg);
}

.logo ion-icon {
  font-size: 52px;
  color: white;
}

.logo-glow {
  position: absolute;
  inset: -12px;
  border-radius: 38px;
  background: var(--app-gradient);
  opacity: 0;
  filter: blur(20px);
  z-index: 1;
  animation: glow-in 1.5s ease-out 0.4s forwards;
}

@keyframes glow-in {
  0% { opacity: 0; transform: scale(0.8); }
  50% { opacity: 0.4; transform: scale(1.1); }
  100% { opacity: 0.25; transform: scale(1); }
}

.logo-ring {
  position: absolute;
  inset: -20px;
  border-radius: 44px;
  border: 2px solid var(--app-primary);
  opacity: 0;
  z-index: 0;
  animation: ring-expand 1.2s ease-out 0.6s forwards;
}

@keyframes ring-expand {
  0% { opacity: 0; transform: scale(0.5); }
  50% { opacity: 0.3; }
  100% { opacity: 0; transform: scale(1.5); }
}

/* Title */
.title {
  font-size: 44px;
  font-weight: 800;
  color: var(--app-text);
  margin: 0;
  letter-spacing: -1px;
  opacity: 0;
  transform: translateY(20px);
  animation: slide-up 600ms cubic-bezier(0.34, 1.56, 0.64, 1) 0.4s forwards;
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Tagline */
.tagline {
  display: flex;
  gap: 8px;
}

.word {
  font-size: 16px;
  color: var(--app-text-muted);
  font-weight: 500;
  letter-spacing: 0.3px;
  opacity: 0;
  transform: translateY(10px);
  animation: slide-up 500ms ease-out forwards;
}

.word-1 { animation-delay: 0.8s; }
.word-2 { animation-delay: 1.0s; }
.word-3 { animation-delay: 1.2s; }

/* Bottom Shimmer */
.bottom-section {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  opacity: 0;
  animation: fade-in 500ms ease-out 1.4s forwards;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.shimmer-bar {
  width: 100%;
  height: 4px;
  background: var(--app-border);
  border-radius: 2px;
  overflow: hidden;
}

.shimmer-fill {
  width: 40%;
  height: 100%;
  background: var(--app-gradient);
  border-radius: 2px;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}
</style>

<template>
  <div class="min-h-screen bg-gradient-to-br from-black via-gray-900 to-emerald-950 flex items-center justify-center px-4 py-8">
    <div class="max-w-md w-full">
      <!-- Logo -->
      <div class="text-center mb-6 sm:mb-8">
        <router-link to="/" class="inline-flex items-center space-x-2">
          <img src="/favicon.png" alt="Echobit" class="w-10 h-10 sm:w-12 sm:h-12 rounded-xl object-contain" />
          <span class="text-2xl sm:text-3xl font-bold text-white">Echobit</span>
        </router-link>
      </div>

      <!-- Register Card -->
      <div class="bg-white/10 backdrop-blur-lg rounded-2xl sm:rounded-3xl p-6 sm:p-8 border border-emerald-500/20 shadow-2xl">
        <h2 class="text-xl sm:text-2xl font-bold text-white mb-2">Create account</h2>
        <p class="text-white/60 mb-6 sm:mb-8 text-sm sm:text-base">Start recording and summarizing for free</p>

        <form @submit.prevent="handleRegister" class="space-y-4 sm:space-y-5">
          <div>
            <label class="block text-white/80 text-sm font-medium mb-2">Full Name</label>
            <input 
              v-model="name" 
              type="text" 
              required
              class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label class="block text-white/80 text-sm font-medium mb-2">Email</label>
            <input 
              v-model="email" 
              type="email" 
              required
              class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label class="block text-white/80 text-sm font-medium mb-2">Password</label>
            <input 
              v-model="password" 
              type="password" 
              required
              minlength="6"
              class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
              placeholder="••••••••"
            />
            <p class="text-white/40 text-xs mt-1">Must be at least 6 characters</p>
          </div>

          <div>
            <label class="block text-white/80 text-sm font-medium mb-2">Confirm Password</label>
            <input 
              v-model="confirmPassword" 
              type="password" 
              required
              class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
              placeholder="••••••••"
            />
          </div>

          <div v-if="error" class="bg-red-500/20 border border-red-500/30 text-red-200 px-4 py-3 rounded-xl text-sm">
            {{ error }}
          </div>

          <button 
            type="submit" 
            :disabled="loading"
            class="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white py-3 rounded-xl font-semibold hover:opacity-90 transition disabled:opacity-50 flex items-center justify-center space-x-2"
          >
            <svg v-if="loading" class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ loading ? 'Creating account...' : 'Create Account' }}</span>
          </button>
        </form>

        <div class="mt-6 sm:mt-8 text-center">
          <p class="text-white/60 text-sm sm:text-base">
            Already have an account? 
            <router-link to="/login" class="text-emerald-400 hover:text-emerald-300 font-medium transition">Sign in</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authApi } from '../api';

const router = useRouter();
const name = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const loading = ref(false);
const error = ref('');

const handleRegister = async () => {
  error.value = '';
  
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match';
    return;
  }

  loading.value = true;
  
  try {
    await authApi.register(name.value, email.value, password.value);
    router.push('/dashboard');
  } catch (err) {
    error.value = err.message || 'Registration failed. Please try again.';
  } finally {
    loading.value = false;
  }
};
</script>

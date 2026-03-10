<template>
  <ion-app>
    <ion-router-outlet />
  </ion-app>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { IonApp, IonRouterOutlet } from '@ionic/vue';
import { App } from '@capacitor/app';

const router = useRouter();

let backButtonHandler: any = null;

onMounted(() => {
  backButtonHandler = App.addListener('backButton', ({ canGoBack }) => {
    const currentRoute = router.currentRoute.value;
    // On home screen, exit the app
    if (currentRoute.name === 'Home' || currentRoute.name === 'Splash') {
      App.exitApp();
    } else if (canGoBack) {
      router.back();
    } else {
      App.exitApp();
    }
  });
});

onUnmounted(() => {
  backButtonHandler?.remove();
});
</script>

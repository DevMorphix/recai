import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'rec.ai',
  appName: 'rec-ai',
  webDir: 'www',
  server: {
    cleartext: true,
    allowNavigation: ['*'],
    // Uncomment below for live reload debugging (run 'npm run dev' first)
    // url: 'http://192.168.1.6:5173',
    // cleartext: true
  },
  plugins: {
    GoogleAuth: {
      scopes: ['profile', 'email'],
      serverClientId: '1004219063159-bhlmuo4cebu9oqf32i6nn2grojmhphh5.apps.googleusercontent.com', // Web client ID from Google Console
      forceCodeForRefreshToken: true,
    },
  },
};

export default config;

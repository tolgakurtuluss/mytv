import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Base path matches the GitHub repo name for GitHub Pages
  base: '/mytv/',
});

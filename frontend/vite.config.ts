import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ['src/**/*.{test,spec}.{js,ts}'],
    environment: 'jsdom',
    setupFiles: ['./src/vitest-setup.ts'],
    poolOptions: {
      threads: {
        execArgv: ['--no-experimental-webstorage'],
      },
      forks: {
        execArgv: ['--no-experimental-webstorage'],
      },
    },
  },
});

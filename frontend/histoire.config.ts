import { HstSvelte } from '@histoire/plugin-svelte';
import { defineConfig } from 'histoire';

export default defineConfig({
  plugins: [HstSvelte()],
  vite: {
    resolve: {
      alias: {
        $lib: new URL('./src/lib', import.meta.url).pathname,
      },
    },
  },
});

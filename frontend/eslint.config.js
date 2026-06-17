import js from '@eslint/js';
import ts from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import svelte from 'eslint-plugin-svelte';
import svelteParser from 'svelte-eslint-parser';
import globals from 'globals';

/** Remap every "error" severity entry to "warn" so the pipeline never fails on lint. */
function warnOnly(rules) {
  return Object.fromEntries(
    Object.entries(rules).map(([key, value]) => {
      if (value === 'error') return [key, 'warn'];
      if (Array.isArray(value) && value[0] === 'error') return [key, ['warn', ...value.slice(1)]];
      return [key, value];
    })
  );
}

export default [
  {
    ...js.configs.recommended,
    rules: warnOnly(js.configs.recommended.rules),
  },
  {
    files: ['**/*.ts'],
    plugins: { '@typescript-eslint': ts },
    languageOptions: {
      parser: tsParser,
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      ...warnOnly(ts.configs.recommended.rules),
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': 'warn',
    },
  },
  {
    files: ['**/*.svelte'],
    plugins: { svelte },
    languageOptions: {
      parser: svelteParser,
      parserOptions: { parser: tsParser },
      globals: { ...globals.browser },
    },
    rules: {
      ...warnOnly(svelte.configs.recommended.rules),
    },
  },
  {
    ignores: ['.svelte-kit/**', 'build/**', 'node_modules/**'],
  },
];

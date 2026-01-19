import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'node:url'
// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  future: { compatibilityVersion: 4 },

  modules: [
    '@nuxt/a11y',
    '@nuxt/eslint',
    '@nuxt/fonts',
    '@nuxt/hints',
    '@nuxt/icon',
    '@nuxt/image',
    '@nuxt/scripts',
    '@nuxt/test-utils',
  ],

  vite: {
    plugins: [tailwindcss()],
  },
  css: ['./app/tailwind.css'],

  typescript: {
    tsConfig: {
      compilerOptions: {
        paths: {
          '@server/*': ['../server/*'],
          '#db/*': ['../server/db/*']
        }
      }
    },
    sharedTsConfig: {
      compilerOptions: {
        paths: {
          '#server/*': ['../server/*']
        }
      }
    },
    nodeTsConfig: {
      compilerOptions: {
        paths: {
          '#server/*': ['../server/*']
        }
      }
    }
  },

  nitro: {
    experimental: {
      tasks: true
    },
    scheduledTasks: {},
    alias: {
      '#server': fileURLToPath(new URL('./server', import.meta.url))
    },
    typescript: {
      tsConfig: {
        compilerOptions: {
          paths: {
            '#server/*': ['../server/*'],
            '#server': ['../server']
          }
        }
      }
    }
  }
})

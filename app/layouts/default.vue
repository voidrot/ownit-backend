<script setup lang="ts">
import { useRouter } from '#imports'
import { authClient } from '~/lib/auth-client'

const year = new Date().getFullYear()

// Session atom from the auth client
// Keep `session` as returned by the client and use template checks.
const session = authClient.useSession()
const router = useRouter()


async function handleSignOut() {
  try {
    await authClient.signOut()
  } finally {
    await router.push('/')
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-base-200 text-base-content">
    <!-- Skip link: hidden offscreen until focused -->
    <a href="#maincontent" class="absolute left-0 -translate-y-full focus:translate-y-0 focus:top-4 focus:left-4 bg-primary text-primary-content px-3 py-2 rounded">Skip to main</a>

    <div class="navbar bg-base-100 shadow-sm">
      <div class="flex-1">
        <NuxtLink class="btn btn-ghost text-xl normal-case" to="/">Ownit</NuxtLink>
      </div>

      <!-- Center nav: only show when authenticated -->
      <div v-if="session && session.data" class="flex-none">
        <ul class="menu menu-horizontal px-1">
          <li v-if="session && session.data && (session.data.user && (session.data.user.role === 'admin' || session.data.user.role === 'parent'))"><NuxtLink to="/admin">Admin</NuxtLink></li>
          <li><NuxtLink to="/profile">Profile</NuxtLink></li>
        </ul>
      </div>

      <!-- Right actions -->
      <div class="flex-none">
        <div v-if="!session || !session.data">
          <NuxtLink to="/login" class="btn btn-primary">Login</NuxtLink>
        </div>
        <div v-else class="flex items-center gap-2">
          <button class="btn btn-outline" @click="handleSignOut">Logout</button>
        </div>
      </div>
    </div>

    <main id="maincontent" class="container mx-auto flex-1 px-4 py-8" role="main" tabindex="-1">
      <slot />
    </main>

    <footer class="footer footer-center p-4 bg-base-100 text-base-content">
      <div class="container mx-auto px-4">
        <p>© <span aria-hidden="true">{{ year }}</span> Ownit</p>
      </div>
    </footer>
  </div>
</template>


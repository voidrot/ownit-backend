<script setup>
import { ref, onMounted, watch } from 'vue'
import { authClient } from '~/lib/auth-client'

const session = authClient.useSession()

const name = ref('')
const image = ref('')
const loading = ref(false)
const message = ref(null)
const error = ref(null)

// Passkey management
const passkeyName = ref('')
const passkeyLoading = ref(false)
const passkeys = authClient.useListPasskeys()
const passkeySupported = ref(false)

// populate fields from session when it hydrates, but do not overwrite user edits
watch(session, (val) => {
  const resolved = val && (val).data && (val).data.user ? (val).data.user : null
  if (resolved) {
    if (!name.value && resolved.name) name.value = resolved.name
    if (!image.value && resolved.image) image.value = resolved.image
  }
}, { immediate: true })

onMounted(async () => {
  // detect WebAuthn / platform authenticator availability (client-only)
  try {
    if (typeof window !== 'undefined' && window.PublicKeyCredential && typeof window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function') {
      passkeySupported.value = await window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
    } else {
      passkeySupported.value = false
    }
  } catch {
    passkeySupported.value = false
  }
})

async function addPasskey() {
  error.value = null
  message.value = null
  passkeyLoading.value = true
  try {
    if (!passkeySupported.value) throw new Error('Passkeys are not supported in this browser')
    const res = await authClient.passkey.addPasskey({ name: passkeyName.value || undefined, useAutoRegister: false }, {
      onSuccess() {
        message.value = 'Passkey registered.'
        passkeyName.value = ''
      },
      onError(ctx) {
        error.value = ctx?.error?.message || 'Passkey registration failed.'
      }
    })
    if (res?.error) {
      error.value = res.error.message || 'Passkey registration failed.'
    }
  } catch (err) {
    error.value = err?.message || 'Passkey registration failed.'
  } finally {
    passkeyLoading.value = false
  }
}

async function deletePasskey(id) {
  error.value = null
  message.value = null
  try {
    const res = await authClient.$fetch('/passkey/delete-passkey', { method: 'POST', body: { id }, throw: false })
    if (res?.error) {
      error.value = res.error.message || 'Failed to delete passkey.'
      return
    }
    message.value = 'Passkey deleted.'
    // plugin atom listener will trigger list refresh, but if not, force a refetch by calling useListPasskeys again
    if (authClient.useListPasskeys) authClient.useListPasskeys()
  } catch (err) {
    error.value = err?.message || 'Failed to delete passkey.'
  }
}

async function save() {
  error.value = null
  message.value = null
  loading.value = true
  try {
    await authClient.updateUser({ name: name.value || undefined, image: image.value || undefined })
    message.value = 'Profile updated.'
  } catch (err) {
    error.value = err?.message || 'Failed to update profile.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="max-w-lg mx-auto p-6">
    <!-- Required by WebAuthn / simplewebauthn: an input with autocomplete containing 'webauthn' -->
    <input id="webauthn-autocomplete" autocomplete="webauthn" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;" aria-hidden="true">
    <h1 class="text-2xl font-semibold mb-4">Profile</h1>

    <div v-if="error" role="alert" class="mb-4 text-sm text-error">{{ error }}</div>
    <div v-if="message" class="mb-4 text-sm text-success">{{ message }}</div>

    <form class="space-y-4" @submit.prevent="save">
      <div>
        <label class="block text-sm font-medium">Name</label>
        <input v-model="name" class="input input-bordered w-full mt-1">
      </div>

      <div>
        <label class="block text-sm font-medium">Image URL</label>
        <input v-model="image" class="input input-bordered w-full mt-1">
      </div>

      <!-- Passkey management -->
      <div>
        <h2 class="text-lg font-medium mt-4">Passkeys</h2>
        <div class="mt-2">
          <div class="flex gap-2 mb-2">
            <input v-model="passkeyName" placeholder="My device" class="input input-bordered flex-1">
            <button type="button" class="btn" :disabled="passkeyLoading || !passkeySupported" @click="addPasskey">{{ passkeyLoading ? 'Registering…' : 'Add passkey' }}</button>
          </div>
          <div v-if="!passkeySupported" class="text-xs text-muted mb-2">Passkeys require a compatible browser and secure context (HTTPS or localhost).</div>

          <ul v-if="passkeys && passkeys.value && passkeys.value.data && passkeys.value.data.length" class="space-y-2">
            <li v-for="pk in passkeys.value.data" :key="pk.id" class="flex items-center justify-between p-2 border rounded">
              <div>
                <div class="font-medium">{{ pk.name || pk.credentialID }}</div>
                <div class="text-xs text-muted">{{ new Date(pk.createdAt).toLocaleString() }}</div>
              </div>
              <div class="flex gap-2">
                <button type="button" class="btn btn-sm btn-error" @click="deletePasskey(pk.id)">Delete</button>
              </div>
            </li>
          </ul>
          <div v-else class="text-sm text-muted">No registered passkeys.</div>
        </div>
      </div>

      <div class="flex gap-2">
        <button class="btn btn-primary" :disabled="loading">{{ loading ? 'Saving…' : 'Save' }}</button>
        <NuxtLink to="/" class="btn btn-ghost">Back</NuxtLink>
      </div>
    </form>
  </main>
</template>

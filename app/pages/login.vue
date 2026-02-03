<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from '#imports'
import { authClient } from '~/lib/auth-client'

const router = useRouter()
const route = useRoute()

const session = authClient.useSession()

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref(null)
const passkeySupported = ref(false)

onMounted(async () => {
    try {
        const isSecure = (typeof window !== 'undefined') && (window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')
        if (!isSecure) {
            passkeySupported.value = false
            return
        }
        if (window.PublicKeyCredential && typeof window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function') {
            passkeySupported.value = await window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
        } else {
            passkeySupported.value = false
        }
    } catch (e) {
        console.debug('WebAuthn detection failed', e)
        passkeySupported.value = false
    }
})

async function onSubmit() {
    error.value = null
    loading.value = true
    try {
        // call the Better Auth signIn.email which returns { data, error }
        const result = await authClient.signIn.email({ email: form.email, password: form.password })
        const signError = result && result.error ? result.error : null
        if (signError) {
            // map common error codes to user-facing messages
            switch (signError.code) {
                case 'INVALID_EMAIL_OR_PASSWORD':
                    error.value = 'Invalid email or password.'
                    break
                case 'EMAIL_NOT_VERIFIED':
                    error.value = 'Please verify your email before signing in.'
                    break
                case 'USER_BANNED':
                    error.value = 'This account has been banned.'
                    break
                default:
                    error.value = signError.message || 'Sign in failed. Please try again.'
            }
            return
        }

        // successful sign-in (data present) — redirect
        const redirectTo = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
        await router.push(redirectTo)
    } catch (err) {
        const message = err && err.message ? err.message : null
        error.value = message || 'Sign in failed. Please check your credentials.'
    } finally {
        loading.value = false
    }
}

// Expose a passkey sign-in action if the client supports it
async function signInWithPasskey() {
    error.value = null
    loading.value = true
    try {
        // Use fetchOptions callbacks to handle passkey flow results client-side
        // add logging to help diagnose failures when passkey isn't working
        console.debug('Starting passkey sign-in')
        await authClient.signIn.passkey({
            autoFill: true,
            fetchOptions: {
                onSuccess() {
                    // redirect after successful passkey auth
                    const redirectTo = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
                    console.debug('Passkey sign-in success, redirecting to', redirectTo)
                    router.push(redirectTo).catch((e) => console.error(e))
                },
                onError(ctx) {
                    console.error('Passkey sign-in error context:', ctx)
                    error.value = ctx?.error?.message || 'Passkey sign-in failed.'
                    // ensure loading is cleared so UI is interactive again
                    loading.value = false
                }
            }
        })
    } catch (err) {
        console.error('Passkey sign-in threw:', err)
        const message = err && err.message ? err.message : null
        error.value = message || 'Passkey sign-in failed.'
    } finally {
        // Only clear loading here if still true; onError callback may have cleared it.
        if (loading.value) loading.value = false
    }
}

// For debugging / informative display during development only
// keep session reactive in template; no-op here
// session may be a reactive atom provided by the auth client
</script>

<template>
    <main class="max-w-md mx-auto p-6">
        <h1 class="text-2xl font-semibold mb-4">Sign in</h1>

        <form novalidate @submit.prevent="onSubmit">
            <div class="mb-4">
                <label for="email" class="block text-sm font-medium">Email</label>
                <input
                    id="email"
                    v-model="form.email"
                    type="email"
                    required
                    autocomplete="email"
                    class="input input-bordered w-full mt-1"
                >
            </div>

            <div class="mb-4">
                <label for="password" class="block text-sm font-medium">Password</label>
                <input
                    id="password"
                    v-model="form.password"
                    type="password"
                    required
                    autocomplete="current-password"
                    class="input input-bordered w-full mt-1"
                >
            </div>

            <!-- Required by WebAuthn / simplewebauthn: an input with autocomplete containing 'webauthn' as the only or last value -->
            <input id="webauthn-autocomplete" autocomplete="webauthn" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;" aria-hidden="true">

            <div v-if="error" role="alert" aria-live="assertive" class="mb-4 text-sm text-error">
                {{ error }}
            </div>

            <div class="flex gap-2 items-center">
                <button class="btn btn-primary" :disabled="loading">
                    <span v-if="!loading">Sign in</span>
                    <span v-else>Signing in…</span>
                </button>
                <button v-if="passkeySupported" type="button" class="btn btn-ghost" :disabled="loading" @click="signInWithPasskey">
                    Sign in with passkey
                </button>
                <button v-else type="button" class="btn btn-ghost btn-disabled" disabled title="Passkeys require a compatible browser and secure context (HTTPS or localhost)">
                    Passkey not supported
                </button>
            </div>
            <p v-if="!passkeySupported" class="text-xs text-muted mt-2">Passkeys require a compatible browser and secure context (HTTPS or localhost).</p>
        </form>

        <section v-if="session && session.value && session.value.data && session.value.data.user" class="mt-6 p-4 bg-base-200 rounded">
            <h2 class="text-sm font-medium">Signed in</h2>
            <p class="text-sm">You are signed in as <strong>{{ session.value.data.user.email || session.value.data.user.id }}</strong>.</p>
        </section>
    </main>
</template>

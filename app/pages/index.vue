<script setup>
import { useRouter } from '#imports'
import { authClient } from '~/lib/auth-client'

const router = useRouter()
const session = authClient.useSession()

async function handleSignOut() {
    try {
        await authClient.signOut()
    } finally {
        await router.push('/')
    }
}
</script>

<template>
    <main class="max-w-3xl mx-auto p-6">
        <h1 class="text-3xl font-bold mb-4">Ownit</h1>

        <p class="mb-6">A simple landing page. Access your account or sign in to manage information.</p>

        <div v-if="!session || !session.data" class="space-y-3">
            <p>You are not signed in.</p>
            <NuxtLink to="/login" class="btn btn-primary">Sign in</NuxtLink>
        </div>

        <div v-else class="space-y-3">
            <p>
                Signed in as
                <strong>
                    {{ session.data.user.name || session.data.user.email || session.data.user.id }}
                </strong>
            </p>

            <div class="flex gap-2 items-center">
                <NuxtLink to="/profile" class="btn">Profile</NuxtLink>
                <button class="btn" @click="handleSignOut">Sign out</button>
                <NuxtLink v-if="session.data.user.role && (session.data.user.role === 'admin' || session.data.user.role === 'parent')" to="/admin" class="btn btn-secondary">Admin</NuxtLink>
            </div>
        </div>
    </main>
</template>

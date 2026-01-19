<script setup lang="ts">
import { authClient } from '~/lib/auth-client'
const session = authClient.useSession
</script>
<template>
    <p>
        {{ session }}
    </p>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { authClient } from '~/lib/auth-client'

type User = {
  id: string
  name?: string | null
  email?: string | null
  role?: string | null
  createdAt?: string | null
}

const users = ref<User[]>([])
const pending = ref(true)
const error = ref<string | null>(null)

// Modal / create form state
const showCreate = ref(false)
const creating = ref(false)
const name = ref('')
const email = ref('')
const password = ref('')
const selectedRoles = ref<string[]>([])
const roleOptions = ['admin', 'parent', 'child']

function resetForm() {
  name.value = ''
  email.value = ''
  password.value = ''
  selectedRoles.value = []
}

async function loadUsers() {
  pending.value = true
  error.value = null
  try {
    const res = await authClient.admin.listUsers({ query: {} })
    const payload = (res as any).data ?? res
    users.value = (payload?.users ?? []) as User[]
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    pending.value = false
  }
}

await loadUsers()

async function createUser() {
  creating.value = true
  error.value = null
  try {
    const body: any = { name: name.value, email: email.value }
    if (password.value) body.password = password.value
    if (selectedRoles.value.length) body.roles = selectedRoles.value

    let res
    try {
      res = await (authClient as any).admin.createUser({
        email: body.email,
        password: body.password,
        name: body.name,
        role: body.roles
      })
    } catch (e) {
      res = await $fetch('/api/auth/admin/users', { method: 'POST', body })
    }

    const payload = (res as any).data ?? res
    const newUser = (payload?.user ?? payload?.users?.[0] ?? res) as User
    if (newUser && (newUser as any).id) users.value.unshift(newUser)
    resetForm()
    showCreate.value = false
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <main class="p-6 max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-semibold">Users</h1>
      <div>
        <label for="create-user-modal" class="btn btn-primary btn-sm" @click.prevent="showCreate = true">Create user</label>
      </div>
    </div>

    <div v-if="error" role="alert" class="text-sm text-error mb-4">{{ error }}</div>
    <div v-if="pending" class="text-sm text-muted">Loading users…</div>

    <table v-if="users && users.length" class="table w-full table-zebra">
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Role</th>
          <th>Created</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="(u as any).id">
          <td>{{ (u as any).name }}</td>
          <td>{{ (u as any).email }}</td>
          <td>{{ (u as any).role || 'user' }}</td>
          <td>{{ (u as any).createdAt }}</td>
        </tr>
      </tbody>
    </table>

    <div v-else-if="!pending" class="text-sm text-muted">No users found.</div>

    <!-- Modal (daisyUI) -->
    <input type="checkbox" id="create-user-modal" class="modal-toggle" v-model="showCreate" />
    <div class="modal">
      <div class="modal-box">
        <h3 class="font-bold text-lg">Create user</h3>
        <div class="py-4 space-y-3">
          <label class="block">
            <span class="label">Name</span>
            <input v-model="name" class="input input-bordered w-full" />
          </label>
          <label class="block">
            <span class="label">Email</span>
            <input v-model="email" type="email" class="input input-bordered w-full" />
          </label>
          <label class="block">
            <span class="label">Password</span>
            <input v-model="password" type="password" class="input input-bordered w-full" />
          </label>
          <fieldset>
            <legend class="label">Roles (choose one or more)</legend>
            <div class="flex gap-3">
              <label v-for="r in roleOptions" :key="r" class="cursor-pointer">
                <input type="checkbox" :value="r" v-model="selectedRoles" class="checkbox mr-2" /> {{ r }}
              </label>
            </div>
          </fieldset>
        </div>
        <div class="modal-action">
          <button class="btn" @click="showCreate = false">Cancel</button>
          <button class="btn btn-primary" :disabled="creating" @click="createUser">Create</button>
        </div>
      </div>
    </div>
  </main>
</template>

<style>

</style>

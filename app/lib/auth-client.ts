import { createAuthClient } from "better-auth/client"
import { passkeyClient } from "@better-auth/passkey/client"
import { adminClient } from "better-auth/client/plugins"
export const authClient = createAuthClient({
    plugins: [
      adminClient(),
      passkeyClient()
    ]
})

export const {
	signIn,
	signOut,
	signUp,
	useSession,
	resetPassword,
	deleteUser
} = authClient

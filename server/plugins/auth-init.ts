import { auth } from "#server/lib/auth"
import { db } from "#server/db"
import { user as userTable } from "#server/db/schema/auth"

export default defineNitroPlugin(async (nitroApp) => {
  // check if any users exist, if not create a default admin user
  try {
    // Check DB directly for existing users — admin endpoints expect request headers.
    const existing = await db.select().from(userTable).limit(1)
    if (existing.length > 0) {
      console.log("Users found in DB, skipping default admin user creation.")
      return
    }
    console.log("No users found. Creating default admin user...")
    // Create default admin user (trusted server context). Uses env vars when provided.
    const resp = await auth.api.createUser({
      body: {
        name: process.env.HOMEBASE_INITIAL_ADMIN_NAME || "Admin User",
        email: process.env.HOMEBASE_INITIAL_ADMIN_EMAIL || "admin@example.com",
        password: process.env.HOMEBASE_INITIAL_ADMIN_PASSWORD || "password",
        role: "admin"
      }
    })
    console.log("Default admin user created:", resp)
  } catch (e) {
    console.error("Error checking users in DB:", e)
    return
  }
})

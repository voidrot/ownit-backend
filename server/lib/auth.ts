import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "#server/db"; // your drizzle instance
import { passkey } from "@better-auth/passkey"
import { admin } from "better-auth/plugins"
import { openAPI } from "better-auth/plugins"
import { expo } from "@better-auth/expo"

export const auth = betterAuth({
    database: drizzleAdapter(db, {
        provider: "pg", // or "mysql", "sqlite"
    }),
    emailAndPassword: {
        enabled: true,
    },
    plugins: [
        passkey(),
        admin(),
        openAPI(),
        expo()
    ],
    trustedOrigins: [
      "homebase://",
      "exp://"
    ]
});
